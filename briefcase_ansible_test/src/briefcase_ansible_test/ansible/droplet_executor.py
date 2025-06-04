"""
Core droplet operations using Ansible - no UI dependencies.
"""

import json
import time
from typing import Dict, Any, Tuple, Optional, List
from dataclasses import dataclass
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible import context
from ansible.module_utils.common.collections import ImmutableDict

from .play_executor import execute_play_with_timeout
from .droplet_metadata import save_droplet_metadata


@dataclass(frozen=True)
class DropletExecutionResult:
    """Immutable result of droplet creation."""

    success: bool
    droplet_id: Optional[str]
    droplet_ip: Optional[str]
    ssh_key_name: Optional[str]
    messages: List[str]
    error: Optional[str] = None


def setup_droplet_vars(
    api_key: str, ssh_key_name: str = "briefcase_ansible"
) -> Dict[str, Any]:
    """Create variables for droplet operations."""
    return {
        "api_token": api_key,  # Fixed variable name
        "ssh_key_name": ssh_key_name,  # Fixed variable name
    }


def execute_ansible_playbook(
    playbook_path: str,
    inventory_path: str,
    extra_vars: Dict[str, Any],
    timeout: int = 300,
) -> Tuple[bool, int, str]:
    """
    Execute Ansible playbook with given variables.

    Returns:
        Tuple of (success, return_code, error_message)
    """
    try:
        # Setup Ansible components
        loader = DataLoader()
        playbook_data = loader.load_from_file(playbook_path)
        inventory = InventoryManager(loader=loader, sources=[inventory_path])
        variable_manager = VariableManager(loader=loader, inventory=inventory)

        # Use Ansible's standard context approach for extra vars
        context.CLIARGS = ImmutableDict(
            connection="local",
            module_path=[],
            forks=1,
            become=None,
            become_method=None,
            become_user=None,
            check=False,
            diff=False,
            verbosity=0,
            host_key_checking=False,
            extra_vars=[json.dumps(extra_vars)],  # JSON serialization for Ansible
        )

        # Load variable manager with context
        variable_manager = VariableManager(loader=loader, inventory=inventory)

        # Create play from playbook data
        if isinstance(playbook_data, list) and playbook_data:
            play_data = playbook_data[0]
        else:
            play_data = playbook_data

        play = Play().load(play_data, variable_manager=variable_manager, loader=loader)

        # Execute playbook
        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=inventory,
                variable_manager=variable_manager,
                loader=loader,
                passwords={},
                stdout_callback=None,
            )

            result = execute_play_with_timeout(tqm, play, None, timeout=timeout)
            success = result == 0
            return (
                success,
                result,
                "" if success else f"Playbook failed with code {result}",
            )

        finally:
            if tqm is not None:
                tqm.cleanup()

    except Exception:
        raise  # Let exceptions propagate


def create_droplet_with_ephemeral_key(
    playbook_path: str,
    inventory_path: str,
    api_key_path: str,
    ssh_keys_dir: str,
    timeout: int = 300,
    metadata_dir_path: Optional[str] = None,
) -> DropletExecutionResult:
    """Create droplet with auto-generated SSH key."""
    messages = []
    timestamp = int(time.time())
    resource_name = f"rtorrent-{timestamp}"

    # Generate ephemeral key
    from briefcase_ansible_test.ssh_utils import generate_ed25519_key

    success, private_key_path, public_key_path, public_key_content = (
        generate_ed25519_key(ssh_keys_dir, None)  # No UI updater
    )

    if not success:
        return DropletExecutionResult(
            success=False,
            droplet_id=None,
            droplet_ip=None,
            ssh_key_name=None,
            messages=[],
            error="Failed to generate SSH key",
        )

    messages.append(f"Generated ephemeral SSH key: {resource_name}")

    # Create droplet with ephemeral key
    result = create_droplet(
        playbook_path=playbook_path,
        inventory_path=inventory_path,
        api_key_path=api_key_path,
        ssh_key_name=resource_name,
        timeout=timeout,
        metadata_dir_path=metadata_dir_path,
    )

    # Add our messages
    all_messages = messages + result.messages

    return DropletExecutionResult(
        success=result.success,
        droplet_id=result.droplet_id,
        droplet_ip=result.droplet_ip,
        ssh_key_name=resource_name if result.success else None,
        messages=all_messages,
        error=result.error,
    )


def create_droplet(
    playbook_path: str,
    inventory_path: str,
    api_key_path: str,
    ssh_key_name: str = "briefcase_ansible",
    timeout: int = 300,
    metadata_dir_path: Optional[str] = None,
) -> DropletExecutionResult:
    """Create a droplet using Ansible playbook."""
    messages = []

    # Read API key - let exceptions propagate
    with open(api_key_path, "r") as f:
        api_key = f.read().strip()

    # Setup variables
    extra_vars = setup_droplet_vars(api_key, ssh_key_name)

    # Execute playbook
    success, return_code, error = execute_ansible_playbook(
        playbook_path, inventory_path, extra_vars, timeout
    )

    if success:
        messages.append("Droplet creation playbook executed successfully")
        # In a real implementation, we'd parse output for droplet details
        droplet_id = "droplet-" + str(int(time.time()))  # Placeholder
        droplet_ip = "pending"  # Would be parsed from output

        # Save metadata if directory provided
        if metadata_dir_path:
            metadata = {
                "droplet_id": droplet_id,
                "droplet_ip": droplet_ip,
                "droplet_name": f"rtorrent-{int(time.time())}",
                "ssh_key_name": ssh_key_name,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "api_key_path": api_key_path,
            }
            save_droplet_metadata(metadata_dir_path, droplet_id, metadata)
            messages.append(f"Metadata saved for droplet {droplet_id}")

        return DropletExecutionResult(
            success=True,
            droplet_id=droplet_id,
            droplet_ip=droplet_ip,
            ssh_key_name=ssh_key_name,
            messages=messages,
            error=None,
        )
    else:
        return DropletExecutionResult(
            success=False,
            droplet_id=None,
            droplet_ip=None,
            ssh_key_name=None,
            messages=messages,
            error=error,
        )


def cleanup_droplet_resources(
    cleanup_playbook_path: str,
    inventory_path: str,
    api_key_path: str,
    droplet_name: str,
    ssh_key_name: str,
    timeout: int = 60,
) -> DropletExecutionResult:
    """Clean up droplet and associated resources."""
    messages = []

    # Read API key
    with open(api_key_path, "r") as f:
        api_key = f.read().strip()

    # Setup cleanup variables
    extra_vars = {
        "api_token": api_key,
        "droplet_name": droplet_name,
        "ssh_key_name": ssh_key_name,
        "action": "destroy",
    }

    # Execute cleanup playbook
    success, return_code, error = execute_ansible_playbook(
        cleanup_playbook_path, inventory_path, extra_vars, timeout
    )

    if success:
        messages.append(f"Cleaned up droplet {droplet_name} and key {ssh_key_name}")
        return DropletExecutionResult(
            success=True,
            droplet_id=None,
            droplet_ip=None,
            ssh_key_name=None,
            messages=messages,
            error=None,
        )
    else:
        return DropletExecutionResult(
            success=False,
            droplet_id=None,
            droplet_ip=None,
            ssh_key_name=None,
            messages=messages,
            error=error,
        )
