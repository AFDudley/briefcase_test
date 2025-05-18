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

# Create a fake pwd module for template/__init__.py
class PwdModule:
    class Struct:
        def __init__(self, **entries):
            self.__dict__.update(entries)
    
    def getpwuid(self, uid):
        return self.Struct(pw_name='mobile')
    
    def getpwnam(self, name):
        return self.Struct(pw_uid=0, pw_gid=0, pw_dir='/home/mobile')

# Install the fake pwd module before Ansible imports
sys.modules['pwd'] = PwdModule()

# Create a patched version of is_executable for iOS
def is_executable(path):
    # On iOS we can't execute files anyway, so we'll fake this
    # based on the file extension and permissions
    if not os.path.exists(path):
        return False
    file_mode = os.stat(path).st_mode
    return (file_mode & stat.S_IXUSR) or path.endswith(('.sh', '.py', '.bin', '.exe'))

# Monkey patch text module before importing Ansible
sys.modules['ansible.module_utils._text'] = type('MockTextModule', (), {
    'to_native': lambda x, errors='strict': str(x),
    'to_bytes': lambda obj, encoding='utf-8', errors='strict': obj.encode(encoding, errors) if isinstance(obj, str) else obj,
    'to_text': lambda obj, encoding='utf-8', errors='strict': obj.decode(encoding, errors) if isinstance(obj, bytes) else str(obj)
})

# Import the real module and override only what's needed
try:
    # Import the real module to use most of its functionality
    import ansible.module_utils.basic as real_basic
    
    # Create a new module that has all the original attributes
    mock_basic = type('MockBasicModule', (), {})
    for attr_name in dir(real_basic):
        if not attr_name.startswith('__'):
            setattr(mock_basic, attr_name, getattr(real_basic, attr_name))
    
    # Override only the problematic function
    mock_basic.is_executable = is_executable
    
    # Replace the module in sys.modules
    sys.modules['ansible.module_utils.basic'] = mock_basic
except ImportError:
    # Fall back to a simpler mock if the import fails
    sys.modules['ansible.module_utils.basic'] = type('MockBasicModule', (), {
        'is_executable': is_executable,
        'json_dict_bytes_to_unicode': lambda d: d if isinstance(d, dict) else {}
    })

# Import Ansible modules directly - skip CLI
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader


class briefcase_ansible_test(toga.App):
    def startup(self):
        """Construct and show the Toga application."""
        # Store a set for background tasks to prevent garbage collection
        self.background_tasks = set()
        
        # Store a reference to the main event loop for background threads
        self.main_event_loop = asyncio.get_event_loop()

        # Create main box with vertical layout
        main_box = toga.Box(style=Pack(direction="column", margin=10))

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
        
        # Button to parse ansible playbook
        parse_playbook_button = toga.Button(
            'Parse Sample Playbook',
            on_press=self.parse_ansible_playbook,
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
        main_box.add(parse_playbook_button)
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

                # Update UI from the main thread
                self.add_text_to_output(f"Found {len(inventory_files)} inventory files\n")

                # Process each inventory file
                for inv_file in inventory_files:
                    self.add_text_to_output(f"Parsing file: {os.path.basename(inv_file)}\n")

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

                    # Update the UI
                    self.add_text_to_output(f"Parsed data:\n{inventory_json}\n\n")

                # Final update when everything is done
                self.add_text_to_output("Inventory parsing completed successfully.\n")
                self.update_status("Completed")

            except Exception as error:
                # Handle any exceptions
                error_message = str(error)
                self.add_text_to_output(f"Error parsing inventory: {error_message}")
                self.update_status("Error")

        # Start background thread
        thread = threading.Thread(target=run_in_background)
        thread.daemon = True
        thread.start()

    def add_text_to_output(self, text):
        """Add text to the output view from any thread."""
        def update_ui():
            self.output_view.value += text
        
        # If we're on the main thread, update directly
        if threading.current_thread() is threading.main_thread():
            update_ui()
        else:
            # Create a direct coroutine for updating the text
            async def update_text():
                self.output_view.value += text
            # Schedule it on the main event loop
            asyncio.run_coroutine_threadsafe(update_text(), self.main_event_loop)
    
    def update_status(self, text):
        """Update the status label from any thread."""
        def update_ui():
            self.status_label.text = text
        
        # If we're on the main thread, update directly
        if threading.current_thread() is threading.main_thread():
            update_ui()
        else:
            # Create a direct coroutine for updating the status
            async def update_status_text():
                self.status_label.text = text
            # Schedule it on the main event loop
            asyncio.run_coroutine_threadsafe(update_status_text(), self.main_event_loop)
    
    def update_output_task(self, text):
        """Returns an async function that appends text to the output view."""
        async def update_output(interface):
            current_text = self.output_view.value
            self.output_view.value = current_text + text
        return update_output
        
    def update_status_task(self, text):
        """Returns an async function that updates the status label."""
        async def update_status_async(interface):
            self.status_label.text = text
        return update_status_async
        
    def parse_ansible_playbook(self, widget):
        """Parse the sample Ansible playbook file and display its JSON structure."""
        # Clear output and update status
        self.output_view.value = ""
        self.status_label.text = "Parsing sample playbook..."

        # Run in a background thread to keep UI responsive
        def run_in_background():
            try:
                # Path to the sample playbook file
                playbook_file = os.path.join(self.paths.app, 'resources', 'playbooks', 'sample_playbook.yml')
                
                self.add_text_to_output(f"Parsing file: sample_playbook.yml\n")

                # Use Ansible's data loader to parse the YAML file
                loader = DataLoader()
                
                # Load the playbook file
                playbook_data = loader.load_from_file(playbook_file)
                
                # Convert playbook data to JSON for display
                playbook_json = json.dumps(playbook_data, indent=2)
                
                # Update the UI with the parsed playbook
                self.add_text_to_output(f"Parsed data:\n{playbook_json}\n\n")

                # Final update when everything is done
                self.add_text_to_output("Playbook parsing completed successfully.\n")
                self.update_status("Completed")

            except Exception as error:
                # Handle any exceptions
                error_message = str(error)
                self.add_text_to_output(f"Error parsing playbook: {error_message}")
                self.update_status("Error")

        # Start background thread
        thread = threading.Thread(target=run_in_background)
        thread.daemon = True
        thread.start()


def main():
    # Return the app instance without calling main_loop()
    # The caller (e.g., __main__.py) will handle calling main_loop()
    return briefcase_ansible_test()
