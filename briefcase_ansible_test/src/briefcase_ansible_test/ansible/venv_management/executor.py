"""
Functional utilities for executing playbooks with virtual environments.
"""

import os
import time
from typing import Dict, Any, Optional, List
from functools import partial

from .metadata import load_venv_metadata, save_venv_metadata

# Imports at module level - no lazy imports
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible import context
from ansible.module_utils.common.collections import ImmutableDict
from ..callbacks import SimpleCallback
from ..play_executor import execute_play_with_timeout


def get_venv_path(venv_name: str, target_host: str, persist: bool = False) -> str:
    """
    Generate the virtual environment path based on persistence setting.

    For persistent venvs, uses ~/ansible-venvs/<name>
    For temporary venvs, uses /tmp/ansible-venv-<name>
    """
    if persist:
        return f"~/ansible-venvs/{venv_name}"
    else:
        return f"/tmp/ansible-venv-{venv_name}"


def create_venv_vars(
    venv_name: str,
    target_host: str,
    persist: bool = False,
    collections: Optional[List[str]] = None,
    python_packages: Optional[List[str]] = None,
    playbook_path: Optional[str] = None,
    extra_vars: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create variables dict for venv wrapper playbook.

    This is a pure function that generates the configuration needed
    for the venv management playbook.
    """
    venv_path = get_venv_path(venv_name, target_host, persist)

    base_vars = {
        "venv_name": venv_name,
        "venv_path": venv_path,
        "persist_venv": persist,
        "target_host": target_host,
        "collect_metadata": True,
        "ansible_collections": collections or [],
        "python_packages": python_packages or ["ansible-core"],
    }

    if playbook_path:
        base_vars["playbook_to_run"] = playbook_path

    if extra_vars:
        base_vars.update(extra_vars)

    return base_vars


def generate_temp_venv_name() -> str:
    """Generate a unique name for a temporary venv."""
    return f"temp_{int(time.time())}"


def create_ansible_context(target_host: str, ssh_key_path: str) -> ImmutableDict:
    """Create Ansible context configuration - pure function."""
    return ImmutableDict(
        connection="ssh" if target_host != "localhost" else "local",
        module_path=[],
        forks=1,
        become=None,
        become_method=None,
        become_user=None,
        check=False,
        diff=False,
        verbosity=0,
        host_key_checking=False,
        ssh_common_args=f"-i {ssh_key_path}" if target_host != "localhost" else "",
    )


def create_default_metadata(wrapper_vars: Dict[str, Any]) -> Dict[str, Any]:
    """Create default metadata structure - pure function."""
    return {
        "venv_name": wrapper_vars.get("venv_name"),
        "venv_path": wrapper_vars.get("venv_path"),
        "target_host": wrapper_vars.get("target_host"),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "persistent": wrapper_vars.get("persist_venv", False),
    }


def run_venv_wrapper_playbook(
    app, wrapper_vars: Dict[str, Any], ui_updater
) -> Dict[str, Any]:
    """
    Execute the venv wrapper playbook and return results.

    Follows functional programming principles with no error hiding.
    """
    # Build paths inline
    playbook_path = os.path.join(
        app.paths.app, "ansible", "venv_management", "playbooks", "venv_wrapper.yml"
    )
    inventory_path = os.path.join(
        app.paths.app, "resources", "inventory", "sample_inventory.ini"
    )
    ssh_key_path = os.path.join(
        app.paths.app, "resources", "keys", "briefcase_test_key"
    )

    # Create data loader and load playbook - let errors propagate
    loader = DataLoader()
    playbook_data = loader.load_from_file(playbook_path)

    # Setup inventory
    inventory = InventoryManager(loader=loader, sources=[inventory_path])

    # Setup variable manager
    variable_manager = VariableManager(loader=loader, inventory=inventory)
    variable_manager.extra_vars = wrapper_vars

    # Configure context
    target_host = wrapper_vars.get("target_host", "localhost")
    context.CLIARGS = create_ansible_context(target_host, ssh_key_path)

    # Create play from playbook
    play_data = playbook_data[0] if isinstance(playbook_data, list) else playbook_data
    play = Play().load(play_data, variable_manager=variable_manager, loader=loader)

    # Create callback
    callback = SimpleCallback(ui_updater)

    # Execute play
    tqm = None
    try:
        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            passwords={},
            stdout_callback=callback,
        )

        result = execute_play_with_timeout(
            tqm, play, ui_updater.add_text_to_output, timeout=300
        )

        # Return result structure
        return {
            "success": result == 0,
            "venv_metadata": create_default_metadata(wrapper_vars),
            "result_code": result,
        }

    finally:
        if tqm is not None:
            tqm.cleanup()


def run_playbook_with_venv(
    app,
    playbook_path: str,
    target_host: str = "night2.lan",
    persist: bool = False,
    venv_name: Optional[str] = None,
    collections: Optional[List[str]] = None,
    python_packages: Optional[List[str]] = None,
    extra_vars: Optional[Dict[str, Any]] = None,
    ui_updater=None,
) -> bool:
    """
    Run a playbook using a virtual environment on the target host.

    This is the main entry point for venv-based playbook execution.
    Returns True if successful, False otherwise.
    """
    # Generate venv name if not provided
    actual_venv_name = venv_name or generate_temp_venv_name()

    # Check for existing venv if persistent
    if persist and venv_name:
        existing = load_venv_metadata(app.paths, actual_venv_name, target_host)
        if existing and ui_updater:
            ui_updater.add_text_to_output(
                f"Using existing venv '{existing['venv_name']}' "
                f"created at {existing['created_at']}\n"
            )

    # Create wrapper variables
    wrapper_vars = create_venv_vars(
        venv_name=actual_venv_name,
        target_host=target_host,
        persist=persist,
        collections=collections,
        python_packages=python_packages,
        playbook_path=playbook_path,
        extra_vars=extra_vars,
    )

    # Execute the wrapper playbook
    result = run_venv_wrapper_playbook(app, wrapper_vars, ui_updater)

    # Save metadata if successful
    if result["success"]:
        metadata = result.get("venv_metadata") if result.get("success") else None
        if metadata:
            save_venv_metadata(app.paths, actual_venv_name, metadata)
            if ui_updater:
                ui_updater.add_text_to_output(
                    f"✅ Metadata saved for venv '{actual_venv_name}'\n"
                )

    return result["success"]


# Convenience functions for common use cases
create_persistent_venv = partial(run_playbook_with_venv, persist=True)
create_temp_venv = partial(run_playbook_with_venv, persist=False)