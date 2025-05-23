"""
Ansible configuration utilities.

This module provides functions to configure Ansible context and settings.
"""

from ansible.module_utils.common.collections import ImmutableDict
from ansible import context
from ansible.plugins.loader import init_plugin_loader


def configure_ansible_context(key_path, connection_type="local", forks=1):
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