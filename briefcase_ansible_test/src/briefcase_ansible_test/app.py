"""
A simple app to parse and display Ansible inventory using Ansible's InventoryManager
"""

import os
import toga
from toga.style import Pack
import threading
import asyncio
import json
import traceback

# Import system utilities
from briefcase_ansible_test.utils.system_utils import (
    patch_getpass,
    setup_pwd_module_mock,
    setup_grp_module_mock,
    setup_ansible_text_module_mock,
    setup_ansible_basic_module_mock
)

# Import SSH utilities
from briefcase_ansible_test.ssh_utils import (
    patch_paramiko_for_async,
    import_paramiko,
    test_ssh_connection
)

# Apply patch for Paramiko's async keyword issue
patch_paramiko_for_async()

# Setup all the module mocks needed for cross-platform compatibility
patch_getpass()
setup_pwd_module_mock()

setup_grp_module_mock()
setup_ansible_text_module_mock()
setup_ansible_basic_module_mock()

# Import Ansible modules directly - skip CLI
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader


class BriefcaseAnsibleTest(toga.App):
    def __init__(self, *args, **kwargs):
        """Construct the Toga application."""
        super().__init__(*args, **kwargs)
        # Store a set for background tasks to prevent garbage collection
        self.background_tasks = set()

    def startup(self):
        """Initialize the application."""
        # Store a reference to the main event loop for background threads
        self.main_event_loop = asyncio.get_event_loop()
        # Create and add action buttons
        action_buttons = self.create_action_buttons()

        # Create output area and status label
        self.output_view, self.status_label = self.create_output_area()

        # Create main layout with all components
        main_box = self.create_main_layout(action_buttons)

        # Create and show the main window
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.size = (600, 400)
        self.main_window.show()

    def create_output_area(self):
        """Create and return the output text area and status label."""
        # Output text area for displaying results
        output_view = toga.MultilineTextInput(
            readonly=True,
            style=Pack(flex=1, margin=5)
        )

        # Status label for showing current state
        status_label = toga.Label(
            'Ready',
            style=Pack(margin=5)
        )

        return output_view, status_label

    def create_main_layout(self, action_buttons):
        """Create and return the main layout with all UI components."""
        # Main box with vertical layout
        main_box = toga.Box(style=Pack(direction="column", margin=10))

        # App title
        title_label = toga.Label(
            'Ansible Inventory Viewer',
            style=Pack(text_align='center', font_size=16, margin=5)
        )

        # Add components to main box
        main_box.add(title_label)
        # Add all action buttons
        for button in action_buttons:
            main_box.add(button)
        main_box.add(self.output_view)
        main_box.add(self.status_label)

        return main_box

    def run_background_task(self, task_func, initial_status="Working..."):
        """
        Execute a function in a background thread with proper error handling.

        Args:
            task_func: The function to execute in the background
            initial_status: The status message to display while task is running
        """
        # Clear output and update status
        self.output_view.value = ""
        self.status_label.text = initial_status

        # Create a wrapper function to handle exceptions
        def background_wrapper():
            try:
                # Execute the actual task
                task_func()
            except Exception as error:
                # Handle any exceptions
                error_message = str(error)
                self.add_text_to_output(f"Error: {error_message}")
                self.update_status("Error")
                # Add traceback for debugging
                self.add_text_to_output(f"\nTraceback:\n{traceback.format_exc()}")

        # Start background thread
        thread = threading.Thread(target=background_wrapper)
        thread.daemon = True
        thread.start()

        # Store the thread to prevent garbage collection
        self.background_tasks.add(thread)

    def create_action_buttons(self):
        """Create and return all action buttons used in the application."""
        buttons = []

        # Button to parse Ansible inventory
        buttons.append(toga.Button(
            'Parse Inventory',
            on_press=self.parse_ansible_inventory,
            style=Pack(margin=5)
        ))

        # Button to parse Ansible playbook
        buttons.append(toga.Button(
            'Parse Playbook',
            on_press=self.parse_ansible_playbook,
            style=Pack(margin=5)
        ))

        # Button to test Paramiko SSH
        buttons.append(toga.Button(
            'Test Paramiko',
            on_press=self.test_paramiko_connection,
            style=Pack(margin=5)
        ))

        # Button to run the sample playbook with Paramiko
        buttons.append(toga.Button(
            'Run Playbook (Paramiko)',
            on_press=self.run_ansible_playbook,
            style=Pack(margin=5)
        ))

        # Button to run Ansible ping test
        buttons.append(toga.Button(
            'Ansible Ping Test',
            on_press=self.ansible_ping_test,
            style=Pack(margin=5)
        ))

        # SSH key buttons removed

        return buttons

    def parse_ansible_inventory(self, widget):
        """Parse Ansible inventory files using InventoryManager directly."""

        # Define the background task function
        def parse_inventory_task():
            # Path to inventory directory
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
                for group_name in inventory.groups:
                    group = inventory.groups[group_name]
                    if group_name != 'all' and group_name != 'ungrouped':
                        inventory_data['all']['children'].append(group_name)
                        inventory_data[group_name] = {'hosts': []}
                        # Add hosts to the group
                        for host in group.get_hosts():
                            inventory_data[group_name]['hosts'].append(host.name)
                            # Store host vars
                            host_vars = {}
                            host_obj = inventory.get_host(host.name)
                            if host_obj is not None:
                                host_vars = host_obj.get_vars()
                            inventory_data['_meta']['hostvars'][host.name] = host_vars

                # Format and display the inventory data
                formatted_data = json.dumps(inventory_data, indent=2)
                self.add_text_to_output(f"Inventory structure:\n{formatted_data}\n\n")

            self.update_status("Completed")

        # Run the task in a background thread
        self.run_background_task(parse_inventory_task, "Parsing inventory...")

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
        """Parse the sample ansible playbook file using Ansible's DataLoader."""

        def parse_playbook_task():
            # Path to the playbook file
            playbook_file = os.path.join(self.paths.app, 'resources', 'playbooks', 'sample_playbook.yml')

            self.add_text_to_output("Parsing file: sample_playbook.yml\n")

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

        # Run the task in a background thread
        self.run_background_task(parse_playbook_task, "Parsing playbook...")

    def test_paramiko_connection(self, widget):
        """Test a basic Paramiko SSH connection."""
        # Clear output and update status
        self.output_view.value = ""
        self.status_label.text = "Testing Paramiko connection..."

        # Define a UI updater object that test_ssh_connection can use
        class UIUpdater:
            def __init__(self, app):
                self.app = app

            def add_text_to_output(self, text):
                self.app.add_text_to_output(text)

            def update_status(self, text):
                self.app.update_status(text)

        # Run in background to keep UI responsive
        def run_in_background():
            # Create a UI updater object
            ui_updater = UIUpdater(self)

            # Run the SSH test
            test_ssh_connection('night2', 'mtm', ui_updater=ui_updater)

        # Run the task in a background thread
        self.run_background_task(run_in_background, "Testing Paramiko connection...")

    def run_ansible_playbook(self, widget):
        """Run the sample Ansible playbook using Paramiko for SSH connections."""
        # Clear output and update status
        self.output_view.value = ""
        self.status_label.text = "Running sample playbook..."

        # Run in a background thread to keep UI responsive
        def run_in_background():
            try:
                # Path to the files
                inventory_file = os.path.join(self.paths.app, 'resources', 'inventory', 'sample_inventory.ini')
                playbook_file = os.path.join(self.paths.app, 'resources', 'playbooks', 'sample_playbook.yml')

                self.add_text_to_output("Loading inventory: sample_inventory.ini\n")
                self.add_text_to_output("Loading playbook: sample_playbook.yml\n")

                # Create data loader
                loader = DataLoader()

                # Set up inventory
                inventory = InventoryManager(loader=loader, sources=[inventory_file])

                # Set up variable manager
                from ansible.vars.manager import VariableManager
                variable_manager = VariableManager(loader=loader, inventory=inventory)

                # Configure connection to use paramiko
                self.add_text_to_output("Configuring Ansible to use Paramiko SSH connections\n")

                # Define a subclass of CallbackBase to capture output
                from ansible.plugins.callback import CallbackBase

                class ResultCallback(CallbackBase):
                    def __init__(self, output_callback):
                        super(ResultCallback, self).__init__()
                        self.output_callback = output_callback

                    def v2_runner_on_ok(self, result):
                        host = result._host.get_name()
                        task = result._task.get_name()
                        self.output_callback(f"✅ {host} | {task} => SUCCESS\n")
                        if 'msg' in result._result:
                            self.output_callback(f"   Message: {result._result['msg']}\n")

                    def v2_runner_on_failed(self, result, ignore_errors=False):
                        host = result._host.get_name()
                        task = result._task.get_name()
                        self.output_callback(f"❌ {host} | {task} => FAILED\n")
                        if 'msg' in result._result:
                            self.output_callback(f"   Error: {result._result['msg']}\n")

                    def v2_runner_on_unreachable(self, result):
                        host = result._host.get_name()
                        self.output_callback(f"🔌 {host} => UNREACHABLE\n")

                    def v2_playbook_on_play_start(self, play):
                        name = play.get_name()
                        self.output_callback(f"▶️ Starting play: {name}\n")

                    def v2_playbook_on_task_start(self, task, is_conditional):
                        name = task.get_name()
                        self.output_callback(f"⏳ Running task: {name}\n")

                # Create a custom callback to receive events
                results_callback = ResultCallback(self.add_text_to_output)

                # Import necessary modules
                from ansible.executor.playbook_executor import PlaybookExecutor
                from ansible import context
                from ansible.utils.context_objects import ImmutableDict

                # Set context.CLIARGS which PlaybookExecutor will use internally
                context.CLIARGS = ImmutableDict(
                    connection='paramiko',    # Use paramiko for SSH connections
                    module_path=None,
                    forks=1,                  # Run tasks serially
                    become=None,
                    become_method=None,
                    become_user=None,
                    check=False,              # Don't perform a dry-run
                    syntax=False,             # Don't just check syntax
                    diff=False,               # Don't show file diffs
                    verbosity=0,              # Minimal output
                    listhosts=False,
                    listtasks=False,
                    listtags=False,
                    ssh_common_args='',
                    ssh_extra_args='',
                    sftp_extra_args='',
                    scp_extra_args='',
                    become_ask_pass=False,
                    remote_user=None,
                    host_key_checking=False   # Disable host key checking
                )

                self.add_text_to_output("Setting up playbook executor...\n")

                # Create playbook executor without passing options directly
                pbex = PlaybookExecutor(
                    playbooks=[playbook_file],
                    inventory=inventory,
                    variable_manager=variable_manager,
                    loader=loader,
                    passwords={}
                )

                # Register our callback if _tqm is available
                if pbex._tqm is not None:
                    pbex._tqm._stdout_callback = results_callback

                self.add_text_to_output("Starting playbook execution with Paramiko transport...\n\n")

                # Run the playbook
                result = pbex.run()

                if result == 0:
                    self.add_text_to_output("\n✨ Playbook execution completed successfully.\n")
                    self.update_status("Completed")
                else:
                    self.add_text_to_output(f"\n⚠️ Playbook execution failed with code {result}.\n")
                    self.update_status("Failed")

            except Exception as error:
                # Handle any exceptions
                error_message = str(error)
                self.add_text_to_output(f"Error executing playbook: {error_message}")
                self.update_status("Error")

        # Start background thread
        thread = threading.Thread(target=run_in_background)
        thread.daemon = True
        thread.start()


    def ansible_ping_test(self, widget):
        """Run an Ansible ping module against night2 to verify SSH connectivity."""
        # Clear output and update status
        self.output_view.value = ""
        self.status_label.text = "Running Ansible ping test..."

        # Run in a background thread to keep UI responsive
        def run_in_background():
            try:
                # Import Ansible modules
                from ansible.module_utils.common.collections import ImmutableDict
                from ansible.parsing.dataloader import DataLoader
                from ansible.inventory.manager import InventoryManager
                from ansible.vars.manager import VariableManager
                from ansible.playbook.play import Play
                from ansible.executor.task_queue_manager import TaskQueueManager
                from ansible.plugins.callback import CallbackBase
                from ansible import context

                # Define a custom callback to capture output
                class ResultCallback(CallbackBase):
                    def __init__(self, output_callback):
                        super(ResultCallback, self).__init__()
                        self.output_callback = output_callback
                        self.host_ok = {}
                        self.host_failed = {}
                        self.host_unreachable = {}

                    def v2_runner_on_ok(self, result):
                        host = result._host.get_name()
                        self.host_ok[host] = result
                        output = f"{host} | SUCCESS => {{\n"
                        output += f"    \"changed\": {str(result._result.get('changed', False)).lower()},\n"
                        if 'ansible_facts' in result._result:
                            output += "    \"ansible_facts\": {\n"
                            for k, v in result._result['ansible_facts'].items():
                                output += "        \"" + str(k) + "\": \"" + str(v) + "\",\n"
                            output += "    },\n"
                        output += "    \"ping\": \"" + str(result._result.get('ping', '')) + "\"\n"
                        output += "}\n"
                        self.output_callback(output)

                    def v2_runner_on_failed(self, result, ignore_errors=False):
                        host = result._host.get_name()
                        self.host_failed[host] = result
                        output = f"{host} | FAILED => {{\n"
                        output += "    \"msg\": \"" + str(result._result.get('msg', 'unknown error')) + "\"\n"
                        output += "}\n"
                        self.output_callback(output)

                    def v2_runner_on_unreachable(self, result):
                                            host = result._host.get_name()
                                            self.host_unreachable[host] = result
                                            output = host + " | UNREACHABLE => {\n"
                                            output += "    \"msg\": \"" + str(result._result.get('msg', 'unreachable')) + "\"\n"
                                            output += "}\n"
                                            self.output_callback(output)

                # Path to the inventory file
                inventory_file = os.path.join(self.paths.app, 'resources', 'inventory', 'sample_inventory.ini')
                self.add_text_to_output("Using inventory: " + inventory_file + "\n")
                self.add_text_to_output("Target: night2\n\n")

                # Setup Ansible objects
                loader = DataLoader()
                inventory = InventoryManager(loader=loader, sources=[inventory_file])
                variable_manager = VariableManager(loader=loader, inventory=inventory)

                # Create and configure options
                context.CLIARGS = ImmutableDict(
                    connection='ssh',
                    module_path=[],
                    forks=10,
                    become=None,
                    become_method=None,
                    become_user=None,
                    check=False,
                    diff=False,
                    verbosity=0
                )

                # Create play with ping task
                play_source = dict(
                    name="Ansible Ping",
                    hosts="night2",
                    gather_facts=False,
                    tasks=[dict(action=dict(module='ping'))]
                )

                # Create the Play
                play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

                # Create callback for output
                results_callback = ResultCallback(self.add_text_to_output)

                # Run it
                tqm = None
                try:
                    tqm = TaskQueueManager(
                        inventory=inventory,
                        variable_manager=variable_manager,
                        loader=loader,
                        passwords=dict(),
                        stdout_callback=results_callback
                    )
                    result = tqm.run(play)

                    if result == 0:
                        self.update_status("Success")
                    else:
                        self.update_status("Failed")

                finally:
                    if tqm is not None:
                        tqm.cleanup()

            except Exception as error:
                self.add_text_to_output(f"Error running Ansible ping: {str(error)}\n")
                self.add_text_to_output(f"Traceback: {traceback.format_exc()}\n")
                self.update_status("Error")

        # Start background thread
        thread = threading.Thread(target=run_in_background)
        thread.daemon = True
        thread.start()





def main():
    # Return the app instance without calling main_loop()
    # The caller (e.g., __main__.py) will handle calling main_loop()
    return BriefcaseAnsibleTest()
