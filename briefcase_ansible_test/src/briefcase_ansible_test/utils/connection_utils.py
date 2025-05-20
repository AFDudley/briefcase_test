"""
Utilities for SSH and Paramiko connections used in Ansible operations.

This module contains extracted SSH and Paramiko-related functionality to reduce the size of app.py.
"""

import os
import threading
import traceback

# Function implementations copied from app.py with minimal changes

def test_paramiko_connection(self, widget):
    """Test a basic Paramiko SSH connection."""
    
    def paramiko_test_task():
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
            self.add_text_to_output("Paramiko is working correctly.\n")

        except paramiko.SSHException as e:
            # This might still be okay depending on the error
            self.add_text_to_output(f"SSH error: {str(e)}\n")
            if "banner exchange" in str(e).lower():
                self.add_text_to_output("Banner exchange attempted! Paramiko is working.\n")
            else:
                self.add_text_to_output("SSH negotiation failed, but socket connection may still be working.\n")

        except Exception as e:
            # Other connection errors
            self.add_text_to_output(f"Connection error: {str(e)}\n")
            self.add_text_to_output("Socket connection failed.\n")

        # Additional tests to check if Paramiko can generate keys
        self.add_text_to_output("\nTesting key generation capability...\n")

        try:
            # Generate a small test key
            key = paramiko.RSAKey.generate(bits=1024)
            self.add_text_to_output(f"Generated RSA key: {key.get_fingerprint().hex()}\n")
        except Exception as e:
            self.add_text_to_output(f"Key generation failed: {str(e)}\n")

        self.update_status("Completed")
    
    # Run the task in a background thread
    self.run_background_task(paramiko_test_task, "Testing Paramiko connection...")

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