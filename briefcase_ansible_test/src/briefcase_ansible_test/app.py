"""
A simple app to parse and display Ansible inventory using Ansible's InventoryManager
"""

import os
import sys
import toga
from toga.style import Pack
import threading
import asyncio
import json
import getpass
import stat

# Create a simple getuser replacement that doesn't need pwd module
def simple_getuser():
    for name in ('LOGNAME', 'USER', 'LNAME', 'USERNAME'):
        user = os.environ.get(name)
        if user:
            return user
    return 'mobile'  # Default iOS user

# Replace getpass.getuser with our simple version
getpass.getuser = simple_getuser

# Create a patched version of is_executable for iOS
def is_executable(path):
    # On iOS we can't execute files anyway, so we'll fake this
    # based on the file extension and permissions
    if not os.path.exists(path):
        return False
    file_mode = os.stat(path).st_mode
    return (file_mode & stat.S_IXUSR) or path.endswith(('.sh', '.py', '.bin', '.exe'))

# Monkey patch is_executable function before importing Ansible
# The real function is defined in ansible/module_utils/basic.py
# We can't use a simple module replacement since this is part of a larger module
sys.modules['ansible.module_utils._text'] = type('MockTextModule', (), {'to_native': lambda x, errors='strict': str(x)})

# We'll define a fake module just for the specific function
class MockBasicModule:
    @staticmethod
    def is_executable(path):
        return is_executable(path)

# Add our mock module to sys.modules
sys.modules['ansible.module_utils.basic'] = MockBasicModule()

# Import Ansible modules directly - skip CLI
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader

# Define direction constants since they may not be available in the current Toga version
COLUMN = "column"
ROW = "row"


class briefcase_ansible_test(toga.App):
    def startup(self):
        """Construct and show the Toga application."""
        # Store a set for background tasks to prevent garbage collection
        self.background_tasks = set()

        # Create main box with vertical layout
        main_box = toga.Box(style=Pack(direction=COLUMN, margin=10))

        # Title
        title_label = toga.Label(
            'Ansible Inventory Viewer',
            style=Pack(text_align='center', font_size=16, margin=5)
        )

        # Button to parse ansible inventory
        run_button = toga.Button(
            'Parse Ansible Inventory',
            on_press=self.parse_ansible_inventory,
            style=Pack(margin=5)
        )

        # Output area
        self.output_view = toga.MultilineTextInput(
            readonly=True,
            style=Pack(flex=1, margin=5)
        )

        # Status label
        self.status_label = toga.Label(
            'Ready',
            style=Pack(margin=5)
        )

        # Add components to main box
        main_box.add(title_label)
        main_box.add(run_button)
        main_box.add(self.output_view)
        main_box.add(self.status_label)

        # Create and show the main window
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.size = (600, 400)
        self.main_window.show()

    def parse_ansible_inventory(self, widget):
        """Parse Ansible inventory files using InventoryManager directly."""
        # Clear output and update status
        self.output_view.value = ""
        self.status_label.text = "Parsing inventory..."

        # Run in a background thread to keep UI responsive
        def run_in_background():
            try:
                # Path to the inventory directory
                inventory_dir = os.path.join(self.paths.app, 'resources', 'inventory')

                # Find all inventory files
                inventory_files = []
                for filename in os.listdir(inventory_dir):
                    if filename.endswith('.ini') or filename.endswith('.yml'):
                        inventory_files.append(os.path.join(inventory_dir, filename))

                self.add_background_task(self.update_output_task(
                    f"Found {len(inventory_files)} inventory files\n"
                ))

                # Process each inventory file
                for inv_file in inventory_files:
                    self.add_background_task(self.update_output_task(
                        f"Parsing file: {os.path.basename(inv_file)}\n"
                    ))

                    # Use Ansible's inventory manager to parse the file
                    loader = DataLoader()
                    inventory = InventoryManager(loader=loader, sources=[inv_file])

                    # Create a dictionary to hold inventory data
                    inventory_data = {'_meta': {'hostvars': {}}, 'all': {'children': []}}

                    # Build inventory structure
                    host_groups = {}
                    for group_name in inventory.groups:
                        group = inventory.groups[group_name]
                        # Skip 'all' and 'ungrouped' special groups
                        if group.name not in ['all', 'ungrouped']:
                            inventory_data[group.name] = {'hosts': []}
                            for host in group.hosts:
                                inventory_data[group.name]['hosts'].append(host.name)
                                # Add host vars
                                inventory_data['_meta']['hostvars'][host.name] = host.vars
                            # Add this group as a child of 'all'
                            inventory_data['all']['children'].append(group.name)

                    # Convert inventory data to JSON
                    inventory_json = json.dumps(inventory_data, indent=2)

                    # Update the UI with the parsed inventory
                    self.add_background_task(self.update_output_task(
                        f"Parsed data:\n{inventory_json}\n\n"
                    ))

                # Final update when everything is done
                async def update_complete():
                    self.output_view.value += "Inventory parsing completed successfully.\n"
                    self.status_label.text = "Completed"

                # Schedule the UI update
                task = asyncio.create_task(update_complete())
                self.background_tasks.add(task)
                task.add_done_callback(self.background_tasks.discard)

            except Exception as error:
                # Handle any exceptions
                error_message = str(error)

                async def update_error():
                    self.output_view.value = f"Error parsing inventory: {error_message}"
                    self.status_label.text = "Error"

                # Schedule the error update
                task = asyncio.create_task(update_error())
                self.background_tasks.add(task)
                task.add_done_callback(self.background_tasks.discard)

        # Start background thread
        thread = threading.Thread(target=run_in_background)
        thread.daemon = True
        thread.start()

    def update_output_task(self, text):
        """Returns an async function that appends text to the output view."""
        async def update_output():
            current_text = self.output_view.value
            self.output_view.value = current_text + text
        return update_output


def main():
    # Return the app instance without calling main_loop()
    # The caller (e.g., __main__.py) will handle calling main_loop()
    return briefcase_ansible_test()
