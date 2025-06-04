"""
Ansible configuration utilities.

This module provides functions to configure Ansible context and settings.
"""

from contextlib import contextmanager
from typing import Optional

from ansible.module_utils.common.collections import ImmutableDict
from ansible import context
from ansible.plugins.loader import init_plugin_loader


def configure_ansible_context(
    key_path: Optional[str], connection_type: str = "local", forks: int = 1
) -> None:
    """
    Configure Ansible CLI arguments and context.

    Args:
        key_path: Path to SSH private key
        connection_type: Connection type (default: "local")
        forks: Number of parallel processes (default: 1)
    """
    context.CLIARGS = ImmutableDict(
        connection=connection_type,
        module_path=[],
        forks=forks,
        become=None,
        become_method=None,
        become_user=None,
        check=False,
        diff=False,
        verbosity=0,
        private_key_file=key_path,
        host_key_checking=False,
    )


def initialize_plugin_loader(output_callback):
    """
    Initialize Ansible plugin loader.

    Args:
        output_callback: Function to call with output messages
    """
    output_callback("Initializing Ansible plugin loader...\n")
    init_plugin_loader()
    output_callback("✅ Plugin loader initialized\n")


def setup_ansible_inventory(inventory_path, loader):
    """
    Set up Ansible inventory.

    Args:
        inventory_path: Path to inventory file
        loader: Ansible DataLoader instance

    Returns:
        tuple: (inventory, variable_manager)
    """
    from ansible.inventory.manager import InventoryManager
    from ansible.vars.manager import VariableManager

    inventory = InventoryManager(loader=loader, sources=[inventory_path])
    variable_manager = VariableManager(loader=loader, inventory=inventory)

    return inventory, variable_manager


@contextmanager
def ansible_task_queue_manager(
    inventory, variable_manager, loader, passwords=None, stdout_callback=None, forks=1
):
    """
    Context manager for Ansible TaskQueueManager with automatic cleanup.

    Args:
        inventory: Ansible inventory object
        variable_manager: Ansible variable manager
        loader: Ansible DataLoader instance
        passwords: Dict of passwords (default: empty dict)
        stdout_callback: Callback for output handling
        forks: Number of parallel processes (default: 1)

    Yields:
        TaskQueueManager: Configured TQM instance

    Ensures:
        - TQM cleanup is always called, even on exceptions
        - Resources are properly released
    """
    from ansible.executor.task_queue_manager import TaskQueueManager

    if passwords is None:
        passwords = dict()

    tqm = None
    try:
        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            passwords=passwords,
            stdout_callback=stdout_callback,
            forks=forks,
        )
        yield tqm
    finally:
        # Always cleanup the TQM, even if an exception occurred
        if tqm is not None:
            tqm.cleanup()
