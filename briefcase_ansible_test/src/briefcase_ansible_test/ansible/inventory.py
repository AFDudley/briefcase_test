"""
Ansible inventory functions for briefcase_ansible_test

This module contains functions for parsing and manipulating Ansible inventory files.
"""

import os
import json

# Ensure system mocks are set up before importing Ansible
from briefcase_ansible_test.utils.system_utils import (
    patch_getpass,
    setup_pwd_module_mock,
    setup_grp_module_mock,
)

# Apply patches that might be needed by Ansible imports
patch_getpass()
setup_pwd_module_mock()
setup_grp_module_mock()

# Now import Ansible modules
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader


def parse_ansible_inventory(app, widget):
    """
    Parse Ansible inventory files using InventoryManager directly.

    Args:
        app: The application instance
        widget: The widget that triggered this function
    """

    # Define the background task function
    def parse_inventory_task():
        # Path to inventory directory
        inventory_dir = os.path.join(app.paths.app, "resources", "inventory")

        # Find all inventory files
        inventory_files = []
        for filename in os.listdir(inventory_dir):
            if filename.endswith(".ini") or filename.endswith(".yml"):
                inventory_files.append(os.path.join(inventory_dir, filename))

        # Update UI from the main thread
        app.ui_updater.add_text_to_output(
            f"Found {len(inventory_files)} inventory files\n"
        )

        # Process each inventory file
        for inv_file in inventory_files:
            app.ui_updater.add_text_to_output(
                f"Parsing file: {os.path.basename(inv_file)}\n"
            )

            # Use Ansible's inventory manager to parse the file
            loader = DataLoader()
            inventory = InventoryManager(loader=loader, sources=[inv_file])

            # Create a dictionary to hold inventory data
            inventory_data = {"_meta": {"hostvars": {}}, "all": {"children": []}}

            # Build inventory structure
            for group_name in inventory.groups:
                group = inventory.groups[group_name]
                if group_name != "all" and group_name != "ungrouped":
                    inventory_data["all"]["children"].append(group_name)
                    inventory_data[group_name] = {"hosts": []}
                    # Add hosts to the group
                    for host in group.get_hosts():
                        inventory_data[group_name]["hosts"].append(host.name)
                        # Store host vars
                        host_vars = {}
                        host_obj = inventory.get_host(host.name)
                        if host_obj is not None:
                            host_vars = host_obj.get_vars()
                        inventory_data["_meta"]["hostvars"][host.name] = host_vars

            # Format and display the inventory data
            formatted_data = json.dumps(inventory_data, indent=2)
            app.ui_updater.add_text_to_output(
                f"Inventory structure:\n{formatted_data}\n\n"
            )

        app.ui_updater.update_status("Completed")

    # Run the task in a background thread
    app.background_task_runner.run_task(parse_inventory_task, "Parsing inventory...")
