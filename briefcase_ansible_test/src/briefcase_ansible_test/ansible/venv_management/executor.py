"""
Functional utilities for executing playbooks with virtual environments.
"""

import os
import time
from typing import Dict, Any, Optional, List
from functools import partial
from dataclasses import dataclass

from .metadata import load_venv_metadata, save_venv_metadata

# Imports at module level - no lazy imports
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible import context
from ansible.module_utils.common.collections import ImmutableDict
from ..play_executor import execute_play_with_timeout


@dataclass(frozen=True)
class VenvExecutionResult:
    """Immutable result of venv-based playbook execution."""
    
    success: bool
    result_code: int
    venv_name: str
    venv_metadata: Optional[Dict[str, Any]]
    messages: List[str]
    existing_metadata: Optional[Dict[str, Any]]
    error: Optional[str] = None


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


def create_ansible_context(target_host: str, ssh_key_path: str) -> Dict[str, Any]:
    """Create Ansible context configuration - pure function."""
    return {
        "connection": "ssh" if target_host != "localhost" else "local",
        "module_path": [],
        "forks": 1,
        "become": None,
        "become_method": None,
        "become_user": None,
        "check": False,
        "diff": False,
        "verbosity": 0,
        "host_key_checking": False,
        "ssh_common_args": f"-i {ssh_key_path}" if target_host != "localhost" else "",
    }


def create_default_metadata(wrapper_vars: Dict[str, Any]) -> Dict[str, Any]:
    """Create default metadata structure - pure function."""
    return {
        "venv_name": wrapper_vars.get("venv_name"),
        "venv_path": wrapper_vars.get("venv_path"),
        "target_host": wrapper_vars.get("target_host"),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "persistent": wrapper_vars.get("persist_venv", False),
    }




def run_playbook_with_venv(
    venv_wrapper_playbook_path: str,
    inventory_path: str,
    ssh_key_path: str,
    metadata_dir_path: str,
    playbook_path: str,
    target_host: str = "night2.lan",
    persist: bool = False,
    venv_name: Optional[str] = None,
    collections: Optional[List[str]] = None,
    python_packages: Optional[List[str]] = None,
    extra_vars: Optional[Dict[str, Any]] = None,
) -> VenvExecutionResult:
    """
    Run a playbook using a virtual environment on the target host.

    This is the main entry point for venv-based playbook execution.
    Returns VenvExecutionResult with all execution details.
    """
    messages = []
    
    # Generate venv name if not provided
    actual_venv_name = venv_name or generate_temp_venv_name()

    # Check for existing venv if persistent
    existing_metadata = None
    if persist and venv_name:
        existing_metadata = load_venv_metadata(metadata_dir_path, actual_venv_name, target_host)
        if existing_metadata:
            messages.append(f"Using existing venv '{existing_metadata['venv_name']}' created at {existing_metadata['created_at']}")

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

    # Execute the wrapper playbook directly using execute_play_with_timeout
    # Create data loader and load playbook - let errors propagate
    loader = DataLoader()
    playbook_data = loader.load_from_file(venv_wrapper_playbook_path)

    # Setup inventory
    inventory = InventoryManager(loader=loader, sources=[inventory_path])

    # Configure context with extra vars
    ansible_context = create_ansible_context(target_host, ssh_key_path)
    # Convert wrapper_vars to the format expected by Ansible's extra_vars
    # Ansible expects extra_vars as a list of strings or files
    import json
    ansible_context['extra_vars'] = [json.dumps(wrapper_vars)]
    context.CLIARGS = ImmutableDict(ansible_context)

    # Setup variable manager (it will automatically load extra_vars from context)
    variable_manager = VariableManager(loader=loader, inventory=inventory)

    # Create play from playbook
    play_data = playbook_data[0] if isinstance(playbook_data, list) else playbook_data
    play = Play().load(play_data, variable_manager=variable_manager, loader=loader)

    # Execute play without UI callbacks (use default Ansible output)
    tqm = None
    try:
        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            passwords={},
            stdout_callback=None,  # Use default, no UI callbacks
        )

        result_code = execute_play_with_timeout(
            tqm, play, None, timeout=300
        )

        success = result_code == 0
        metadata = None

        # Save metadata if successful
        if success:
            metadata = create_default_metadata(wrapper_vars)
            save_venv_metadata(metadata_dir_path, actual_venv_name, metadata)
            messages.append(f"Metadata saved for venv '{actual_venv_name}'")

        return VenvExecutionResult(
            success=success,
            result_code=result_code,
            venv_metadata=metadata,
            messages=messages,
            venv_name=actual_venv_name,
            existing_metadata=existing_metadata
        )

    finally:
        if tqm is not None:
            tqm.cleanup()


# Convenience functions for common use cases
# Note: These need to be updated by callers to provide the required paths
# create_persistent_venv = partial(run_playbook_with_venv, persist=True)
# create_temp_venv = partial(run_playbook_with_venv, persist=False)