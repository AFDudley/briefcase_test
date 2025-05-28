"""
Inventory debugging utilities for Ansible.

This module provides functions to debug and display Ansible inventory contents.
"""


def debug_inventory_contents(inventory, target_host, output_callback):
    """
    Debug and display inventory contents.

    Args:
        inventory: Ansible InventoryManager instance
        target_host: Target host pattern to match
        output_callback: Function to call with output messages

    Returns:
        list: List of hosts matching the target pattern
    """
    # Debug inventory contents
    all_hosts = inventory.get_hosts()
    output_callback(f"Found {len(all_hosts)} total hosts in inventory\n")
    for host in all_hosts:
        output_callback(f"  Host: {host.name}\n")

    # Check if target host pattern matches any hosts
    target_hosts = inventory.get_hosts(pattern=target_host)
    output_callback(f"Hosts matching '{target_host}': {len(target_hosts)}\n")
    for host in target_hosts:
        output_callback(f"  Matched host: {host.name}\n")

    return target_hosts


def debug_inventory_groups(inventory, output_callback):
    """
    Debug and display inventory groups.

    Args:
        inventory: Ansible InventoryManager instance
        output_callback: Function to call with output messages
    """
    groups = inventory.get_groups_dict()
    output_callback(f"Inventory groups: {list(groups.keys())}\n")
    for group_name, hosts in groups.items():
        output_callback(f"  Group '{group_name}': {hosts}\n")
