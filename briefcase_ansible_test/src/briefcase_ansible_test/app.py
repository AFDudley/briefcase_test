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

# Setup all the module mocks needed for cross-platform compatibility
patch_getpass()
setup_pwd_module_mock()

setup_grp_module_mock()
setup_ansible_text_module_mock()
setup_ansible_basic_module_mock()

# Import Ansible modules directly - skip CLI
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader


class briefcase_ansible_test(toga.App):
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

        # Button to generate ED25519 key
        buttons.append(toga.Button(
            'Generate ED25519 Key',
            on_press=self.generate_ed25519_key,
            style=Pack(margin=5)
        ))

        # Button to run Ansible ping with key
        buttons.append(toga.Button(
            'Ping with ED25519 Key',
            on_press=self.ansible_ping_test_with_key,
            style=Pack(margin=5)
        ))
        
        return buttons
        
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

            except Exception as error:
                # Handle any exceptions
                error_message = str(error)
                self.add_text_to_output(f"Error parsing playbook: {error_message}")
                self.update_status("Error")

        # Start background thread
        thread = threading.Thread(target=run_in_background)
        thread.daemon = True
        thread.start()

    def test_paramiko_connection(self, widget):
        """Test a basic Paramiko SSH connection."""
        # Clear output and update status
        self.output_view.value = ""
        self.status_label.text = "Testing Paramiko connection..."

        # Run in a background thread to keep UI responsive
        def run_in_background():
            try:
                import paramiko

                paramiko_version = getattr(paramiko, "__version__", "unknown")
                self.add_text_to_output("Paramiko version: " + paramiko_version + "\n")
                self.add_text_to_output("Initializing SSH client...\n")

                # Create a client instance
                client = paramiko.SSHClient()

                # Auto-accept host keys
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                # Connection parameters - using localhost for testing
                hostname = '127.0.0.1'
                username = 'mobile'  # Use a default username
                port = 22

                # For testing, we'll just attempt the connection but not authenticate
                # This will test if Paramiko can create a socket connection
                self.add_text_to_output(f"Connecting to {hostname}:{port} as {username}...\n")

                try:
                    # Try to connect with a short timeout
                    # We expect this to fail due to authentication, but it will show
                    # that the basic socket connection works
                    client.connect(
                        hostname=hostname,
                        username=username,
                        port=port,
                        timeout=2,
                        allow_agent=False,
                        look_for_keys=False
                    )

                    self.add_text_to_output("Connection successful! This is unexpected.\n")
                    client.close()

                except paramiko.AuthenticationException:
                    # This is actually good - means the socket connection worked
                    # but authentication failed as expected
                    self.add_text_to_output("Authentication failed as expected. Socket connection works!\n")
                    self.add_text_to_output("✅ Paramiko is working correctly.\n")

                except paramiko.SSHException as e:
                    # This might still be okay depending on the error
                    self.add_text_to_output(f"SSH error: {str(e)}\n")
                    if "banner exchange" in str(e).lower():
                        self.add_text_to_output("✅ Banner exchange attempted! Paramiko is working.\n")
                    else:
                        self.add_text_to_output("⚠️ SSH negotiation failed, but socket connection may still be working.\n")

                except Exception as e:
                    # Other connection errors
                    self.add_text_to_output(f"Connection error: {str(e)}\n")
                    self.add_text_to_output("❌ Socket connection failed.\n")

                # Additional tests to check if Paramiko can generate keys
                self.add_text_to_output("\nTesting key generation capability...\n")

                try:
                    # Generate a small test key
                    key = paramiko.RSAKey.generate(bits=1024)
                    self.add_text_to_output(f"✅ Generated RSA key: {key.get_fingerprint().hex()}\n")
                except Exception as e:
                    self.add_text_to_output(f"❌ Key generation failed: {str(e)}\n")

                self.update_status("Completed")

            except ImportError as e:
                self.add_text_to_output(f"Error importing Paramiko: {str(e)}\n")
                self.add_text_to_output("❌ Paramiko is not available in this environment.\n")
                self.update_status("Failed")

            except Exception as e:
                # Handle any other exceptions
                self.add_text_to_output(f"Unexpected error: {str(e)}\n")
                self.update_status("Error")

        # Start background thread
        thread = threading.Thread(target=run_in_background)
        thread.daemon = True
        thread.start()

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


    def create_ssh_directory(self):
        """Create a directory for SSH keys if it doesn't exist."""
        ssh_dir = os.path.join(self.paths.app, 'resources', 'ssh')
        if not os.path.exists(ssh_dir):
            os.makedirs(ssh_dir, exist_ok=True)
        return ssh_dir

    def generate_ed25519_key(self, widget):
        """Generate a new ED25519 SSH key and save it to the app resources."""
        # Clear output and update status
        self.output_view.value = ""
        self.status_label.text = "Generating ED25519 SSH key..."

        # Run in a background thread to keep UI responsive
        def run_in_background():
            try:
                from cryptography.hazmat.primitives.asymmetric import ed25519
                from cryptography.hazmat.primitives import serialization
                import paramiko

                self.add_text_to_output("Generating new ED25519 key pair...\n")

                # Create the SSH directory
                ssh_dir = self.create_ssh_directory()

                # Generate a new ED25519 private key
                private_key = ed25519.Ed25519PrivateKey.generate()

                # Get the public key (used to create the public key file)
                private_key.public_key()

                # Serialize the private key to PEM format
                private_key_pem = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.OpenSSH,
                    encryption_algorithm=serialization.NoEncryption()
                )

                # Save the private key
                private_key_path = os.path.join(ssh_dir, 'id_ed25519')
                with open(private_key_path, 'wb') as f:
                    f.write(private_key_pem)

                # Make sure permissions are set correctly (600)
                os.chmod(private_key_path, 0o600)

                # Create the public key in OpenSSH format
                # We'll use paramiko to help with this
                pk = paramiko.Ed25519Key(data=private_key_pem)
                public_key_str = f"{pk.get_name()} {pk.get_base64()} ansible-briefcase-app"

                # Save the public key
                public_key_path = os.path.join(ssh_dir, 'id_ed25519.pub')
                with open(public_key_path, 'w') as f:
                    f.write(public_key_str)
                    f.write('\n')

                # Display information about the generated key
                self.add_text_to_output("Generated ED25519 key pair:\n")
                self.add_text_to_output("Private key: " + private_key_path + "\n")
                self.add_text_to_output("Public key: " + public_key_path + "\n\n")

                # Display the public key for the user to copy
                self.add_text_to_output("Public Key (add this to authorized_keys on your server):\n")
                self.add_text_to_output(f"{public_key_str}\n\n")

                # Display fingerprint
                fingerprint = pk.get_fingerprint().hex()
                self.add_text_to_output(f"Key Fingerprint: {':'.join([fingerprint[i:i+2] for i in range(0, len(fingerprint), 2)])}\n")

                self.update_status("Key Generated")

            except ImportError as e:
                self.add_text_to_output(f"Error importing required modules: {str(e)}\n")
                self.add_text_to_output("Make sure 'cryptography' and 'paramiko' are installed.\n")
                self.update_status("Failed")

            except Exception as e:
                self.add_text_to_output(f"Error generating key: {str(e)}\n")
                self.add_text_to_output(f"Traceback: {traceback.format_exc()}\n")
                self.update_status("Error")

        # Start background thread
        thread = threading.Thread(target=run_in_background)
        thread.daemon = True
        thread.start()

    def ansible_ping_test_with_key(self, widget):
        """Run an Ansible ping module against night2 using the ED25519 key."""
        # Clear output and update status
        self.output_view.value = ""
        self.status_label.text = "Running Ansible ping test with ED25519 key..."

        # Run in a background thread to keep UI responsive
        def run_in_background():
            try:
                # Check if we have a key
                ssh_dir = os.path.join(self.paths.app, 'resources', 'ssh')
                private_key_path = os.path.join(ssh_dir, 'id_ed25519')

                if not os.path.exists(private_key_path):
                    self.add_text_to_output("ED25519 private key not found.\n")
                    self.add_text_to_output(f"Expected path: {private_key_path}\n")
                    self.add_text_to_output("Please generate a key first.\n")
                    self.update_status("Failed")
                    return

                # Make sure the permissions are correct (iOS may have reset them)
                os.chmod(private_key_path, 0o600)
                self.add_text_to_output("Using private key: " + private_key_path + "\n")

                # Import Ansible modules
                from ansible.module_utils.common.collections import ImmutableDict
                from ansible.parsing.dataloader import DataLoader
                from ansible.inventory.manager import InventoryManager
                from ansible.vars.manager import VariableManager
                from ansible.playbook.play import Play
                from ansible.executor.task_queue_manager import TaskQueueManager
                from ansible.plugins.callback import CallbackBase
                from ansible import context

                # Define callback to capture output (same as before)
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
                                                    output += f"        \"{k}\": \"{v}\",\n"
                                                output += "    },\n"
                                            output += f"    \"ping\": \"{result._result.get('ping', '')}\"\n"
                                            output += "}\n"
                                            self.output_callback(output)

                    def v2_runner_on_failed(self, result, ignore_errors=False):
                                            host = result._host.get_name()
                                            self.host_failed[host] = result
                                            output = f"{host} | FAILED => {{\n"
                                            output += f"    \"msg\": \"{result._result.get('msg', 'unknown error')}\"\n"
                                            output += "}\n"
                                            self.output_callback(output)

                    def v2_runner_on_unreachable(self, result):
                        host = result._host.get_name()
                        self.host_unreachable[host] = result
                        output = f"{host} | UNREACHABLE => {{\n"
                        output += f"    \"msg\": \"{result._result.get('msg', 'unreachable')}\"\n"
                        output += "}\n"
                        self.output_callback(output)

                # Path to the inventory file
                inventory_file = os.path.join(self.paths.app, 'resources', 'inventory', 'sample_inventory.ini')
                self.add_text_to_output(f"Using inventory: {inventory_file}\n")
                self.add_text_to_output("Target: night2\n\n")

                # Setup Ansible objects
                loader = DataLoader()
                inventory = InventoryManager(loader=loader, sources=[inventory_file])
                variable_manager = VariableManager(loader=loader, inventory=inventory)

                # Create and configure options with SSH key
                context.CLIARGS = ImmutableDict(
                    connection='ssh',
                    module_path=[],
                    forks=10,
                    become=None,
                    become_method=None,
                    become_user=None,
                    check=False,
                    diff=False,
                    verbosity=0,
                    private_key_file=private_key_path
                )

                # private_key_file parameter in CLIARGS will be used by Ansible

                # Create play with ping task
                play_source = dict(
                    name="Ansible Ping with ED25519 Key",
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
    return briefcase_ansible_test()
