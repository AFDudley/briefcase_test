"""
A simple app to parse and display Ansible inventory using Ansible's InventoryManager
"""

# Standard library imports
import os
import asyncio
import logging
import datetime

# Third-party imports
import toga

# Local application imports
from briefcase_ansible_test.ansible import (
    parse_ansible_inventory,
    parse_ansible_playbook,
    run_ansible_playbook,
    ansible_ping_test,
)
from briefcase_ansible_test.ssh_utils import test_ssh_connection
from briefcase_ansible_test.ui import BackgroundTaskRunner, UIComponents, UIUpdater


class BriefcaseAnsibleTest(toga.App):
    def __init__(self, *args, **kwargs):
        """Construct the Toga application."""
        super().__init__(*args, **kwargs)
        # Store a set for background tasks to prevent garbage collection
        self.background_tasks = set()
        self.logger = None

    def setup_logging(self):
        """Set up global logging to file in the app's resource directory."""
        try:
            # Create logs directory in the app's resource folder
            logs_dir = os.path.join(self.paths.app, "logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            # Create log file with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(logs_dir, f"briefcase_ansible_test_{timestamp}.log")
            
            # Set up root logger to capture everything
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.DEBUG)
            
            # Remove any existing handlers
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
            
            # File handler for all logs
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            root_logger.addHandler(file_handler)
            
            # Set up app-specific logger
            self.logger = logging.getLogger("BriefcaseAnsibleTest")
            
            # Set up global exception handler
            def handle_exception(exc_type, exc_value, exc_traceback):
                if issubclass(exc_type, KeyboardInterrupt):
                    sys.__excepthook__(exc_type, exc_value, exc_traceback)
                    return
                
                logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
            
            import sys
            sys.excepthook = handle_exception
            
            self.logger.info(f"Global logging initialized. Log file: {log_file}")
            return log_file
            
        except Exception as e:
            print(f"Failed to set up logging: {e}")
            return None

    def log_error(self, message, exception=None):
        """Log an error message and optional exception."""
        if self.logger:
            if exception:
                self.logger.error(f"{message}: {exception}", exc_info=True)
            else:
                self.logger.error(message)
        else:
            print(f"LOG ERROR: {message}")
            if exception:
                print(f"EXCEPTION: {exception}")

    def log_info(self, message):
        """Log an info message."""
        if self.logger:
            self.logger.info(message)
        else:
            print(f"LOG INFO: {message}")

    def startup(self):
        """Initialize the application."""
        # Set up logging first
        log_file = self.setup_logging()
        
        # Store a reference to the main event loop for background threads
        self.main_event_loop = asyncio.get_event_loop()
        # Import test functions
        from .test_multiprocessing import test_multiprocessing
        from .test_worker_import import test_worker_import
        from .test_display_import import test_display_import
        from .test_task_executor_imports import test_task_executor_imports
        from .test_direct_import import test_direct_import
        from .test_module_level_sim import test_module_level_sim
        from .test_import_trace import test_import_trace
        from .test_ansible_workerprocess import test_ansible_workerprocess
        from .test_simple_workerprocess import test_simple_workerprocess
        from .test_ssh_connection import test_ssh_connection
        from .test_ios_multiprocessing_integration import test_ios_multiprocessing_integration
        
        # Key generation functions
        def generate_ed25519_key_cryptography(ui_updater):
            """Generate an ed25519 SSH key pair using cryptography library"""
            try:
                from cryptography.hazmat.primitives import serialization
                from cryptography.hazmat.primitives.asymmetric import ed25519
                import base64
                import hashlib
                
                ui_updater.add_text_to_output("Generating ed25519 key pair using cryptography...\n")
                
                # Generate the private key
                private_key = ed25519.Ed25519PrivateKey.generate()
                
                # Get the public key
                public_key = private_key.public_key()
                
                # Serialize private key in OpenSSH format (compatible with paramiko 2.2.1)
                private_key_bytes = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.OpenSSH,
                    encryption_algorithm=serialization.NoEncryption()
                )
                
                # Serialize public key in OpenSSH format
                public_key_bytes = public_key.public_bytes(
                    encoding=serialization.Encoding.OpenSSH,
                    format=serialization.PublicFormat.OpenSSH
                )
                
                # Generate fingerprint (SHA256)
                public_key_raw = public_key.public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw
                )
                fingerprint = base64.b64encode(hashlib.sha256(public_key_raw).digest()).decode().rstrip('=')
                
                ui_updater.add_text_to_output(f"✓ Generated ed25519 key\n")
                ui_updater.add_text_to_output(f"✓ Fingerprint: SHA256:{fingerprint}\n")
                ui_updater.add_text_to_output(f"✓ Full public key:\n{public_key_bytes.decode()}\n")
                ui_updater.add_text_to_output(f"✓ Private key length: {len(private_key_bytes)} bytes\n")
                
                # Store the generated keys in the app instance
                self.generated_private_key = private_key_bytes.decode()
                self.generated_public_key = public_key_bytes.decode()
                ui_updater.add_text_to_output("✓ Keys stored in memory for testing\n")
                
                # Test paramiko compatibility (Ed25519 support varies by version)
                import paramiko
                
                if hasattr(paramiko, 'Ed25519Key'):
                    from io import StringIO
                    
                    try:
                        # Try the newer API first
                        private_key_file = StringIO(private_key_bytes.decode())
                        paramiko_key = paramiko.Ed25519Key.from_private_key(private_key_file)
                        ui_updater.add_text_to_output("✓ Successfully created paramiko Ed25519Key object\n")
                    except TypeError:
                        # Fall back to older paramiko API (2.2.1)
                        import tempfile
                        import os
                        
                        # Write to temporary file for older paramiko
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as temp_file:
                            temp_file.write(private_key_bytes.decode())
                            temp_path = temp_file.name
                        
                        try:
                            paramiko_key = paramiko.Ed25519Key.from_private_key_file(temp_path)
                            ui_updater.add_text_to_output("✓ Successfully created paramiko Ed25519Key object\n")
                        except Exception as e:
                            ui_updater.add_text_to_output(f"⚠ Could not load into paramiko Ed25519Key: {e}\n")
                        finally:
                            os.unlink(temp_path)
                    except Exception as e:
                        ui_updater.add_text_to_output(f"⚠ Could not load into paramiko Ed25519Key: {e}\n")
                else:
                    ui_updater.add_text_to_output("⚠ This paramiko version doesn't support Ed25519Key\n")
                ui_updater.add_text_to_output("✓ Cryptography key generation completed successfully!\n")
                
            except Exception as e:
                ui_updater.add_text_to_output(f"✗ Cryptography key generation failed: {e}\n")
                import traceback
                ui_updater.add_text_to_output(f"Traceback:\n{traceback.format_exc()}\n")

        def generate_ed25519_key_paramiko(ui_updater):
            """Generate ed25519 key using paramiko directly"""
            try:
                import paramiko
                from io import StringIO
                
                ui_updater.add_text_to_output("Generating ed25519 key pair using paramiko...\n")
                
                # Generate the key
                key = paramiko.Ed25519Key.generate()
                
                # Get public key in OpenSSH format
                public_key = f"ssh-ed25519 {key.get_base64()}"
                
                # Get private key
                private_key_file = StringIO()
                key.write_private_key(private_key_file)
                private_key = private_key_file.getvalue()
                
                # Get fingerprint
                fingerprint = key.get_fingerprint().hex()
                
                ui_updater.add_text_to_output(f"✓ Generated ed25519 key\n")
                ui_updater.add_text_to_output(f"✓ Fingerprint: MD5:{':'.join(fingerprint[i:i+2] for i in range(0, len(fingerprint), 2))}\n")
                ui_updater.add_text_to_output(f"✓ Public key: {public_key[:50]}...\n")
                ui_updater.add_text_to_output(f"✓ Private key length: {len(private_key)} chars\n")
                ui_updater.add_text_to_output("✓ Paramiko key generation completed successfully!\n")
                
            except Exception as e:
                ui_updater.add_text_to_output(f"✗ Paramiko key generation failed: {e}\n")
                import traceback
                ui_updater.add_text_to_output(f"Traceback:\n{traceback.format_exc()}\n")

        # Store generated key in app instance for testing
        self.generated_private_key = None
        self.generated_public_key = None
        
        def test_ssh_connection_generated_key(ui_updater):
            """Test SSH connection using generated ed25519 key"""
            try:
                ui_updater.add_text_to_output("Testing SSH Connection with generated key...\n")
                
                # Check if we have a generated key
                if not self.generated_private_key:
                    ui_updater.add_text_to_output("❌ No generated key found. Please generate a key first using 'Generate Key (Cryptography)' button.\n")
                    return
                
                # Apply iOS patches first
                ui_updater.add_text_to_output("Setting up iOS patches...\n")
                
                import ios_multiprocessing
                from briefcase_ansible_test.utils import (
                    setup_pwd_module_mock,
                    setup_grp_module_mock,
                    patch_getpass,
                    setup_subprocess_mock,
                )
                
                ios_multiprocessing.patch_system_modules()
                setup_pwd_module_mock()
                setup_grp_module_mock()
                patch_getpass()
                setup_subprocess_mock()
                
                ui_updater.add_text_to_output("✅ iOS patches applied\n")
                
                # Display the public key
                ui_updater.add_text_to_output(f"📋 Using generated ed25519 public key:\n{self.generated_public_key}\n")
                ui_updater.add_text_to_output("💡 Make sure this key is added to ~/.ssh/authorized_keys for user 'mtm' on night2.lan\n")
                
                # Test Paramiko SSH connection with generated key
                ui_updater.add_text_to_output("🔧 Testing Paramiko SSH connection with generated key...\n")
                
                import paramiko
                from io import StringIO
                ui_updater.add_text_to_output("✅ Paramiko imported\n")
                
                # Create SSH client
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ui_updater.add_text_to_output("✅ SSH client created\n")
                
                # Load generated private key using temp file (paramiko 2.2.1 requirement)
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as temp_file:
                    temp_file.write(self.generated_private_key)
                    temp_path = temp_file.name
                
                private_key = paramiko.Ed25519Key.from_private_key_file(temp_path)
                os.unlink(temp_path)
                ui_updater.add_text_to_output("✅ Generated ed25519 private key loaded successfully\n")
                
                # Connect using generated key
                ui_updater.add_text_to_output("🚀 Attempting SSH connection to night2.lan...\n")
                ui_updater.add_text_to_output("User: mtm\n")
                ui_updater.add_text_to_output("Key: [Generated ed25519 key from memory]\n")
                
                ssh_client.connect(
                    hostname="night2.lan",
                    username="mtm", 
                    pkey=private_key,
                    timeout=10
                )
                
                ui_updater.add_text_to_output("✅ SSH connection successful!\n")
                
                # Test command execution
                ui_updater.add_text_to_output("📋 Testing command execution...\n")
                stdin, stdout, stderr = ssh_client.exec_command('echo "Hello from SSH with generated key"')
                
                output = stdout.read().decode().strip()
                ui_updater.add_text_to_output(f"Command output: {output}\n")
                ui_updater.add_text_to_output("✅ Command execution successful!\n")
                
                # Close connection
                ssh_client.close()
                ui_updater.add_text_to_output("✅ SSH connection closed\n")
                ui_updater.add_text_to_output("✅ Generated key SSH connection test complete.\n")
                
            except Exception as e:
                ui_updater.add_text_to_output(f"❌ Generated key SSH connection failed: {e}\n")
                import traceback
                ui_updater.add_text_to_output(f"Traceback:\n{traceback.format_exc()}\n")

        def run_droplet_playbook(ui_updater):
            """Run the rtorrent droplet creation playbook from night2"""
            try:
                ui_updater.add_text_to_output("Starting rtorrent droplet creation...\n")
                
                # Apply iOS patches first
                ui_updater.add_text_to_output("Setting up iOS patches...\n")
                
                import ios_multiprocessing
                from briefcase_ansible_test.utils import (
                    setup_pwd_module_mock,
                    setup_grp_module_mock,
                    patch_getpass,
                    setup_subprocess_mock,
                )
                
                ios_multiprocessing.patch_system_modules()
                setup_pwd_module_mock()
                setup_grp_module_mock()
                patch_getpass()
                setup_subprocess_mock()
                
                ui_updater.add_text_to_output("✅ iOS patches applied\n")
                
                # Load the API key
                api_key_file = os.path.join(
                    self.paths.app, "resources", "api_keys", "do.api_key"
                )
                with open(api_key_file, 'r') as f:
                    api_key = f.read().strip()
                ui_updater.add_text_to_output("✅ Digital Ocean API key loaded\n")
                
                # Set up SSH connection to night2
                import paramiko
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # Use the briefcase_test_key for SSH
                key_path = os.path.join(
                    self.paths.app, "resources", "keys", "briefcase_test_key"
                )
                private_key = paramiko.RSAKey.from_private_key_file(key_path)
                ui_updater.add_text_to_output("✅ SSH key loaded\n")
                
                # Connect to night2
                ui_updater.add_text_to_output("Connecting to night2.lan...\n")
                ssh_client.connect(
                    hostname="night2.lan",
                    username="mtm",
                    pkey=private_key,
                    timeout=10
                )
                ui_updater.add_text_to_output("✅ Connected to night2.lan\n")
                
                # Copy the playbook to night2 temporarily
                playbook_path = os.path.join(
                    self.paths.app, "resources", "playbooks", "start_rtorrent_droplet.yml"
                )
                with open(playbook_path, 'r') as f:
                    playbook_content = f.read()
                
                # Create a temporary file on night2
                ui_updater.add_text_to_output("Copying playbook to night2...\n")
                stdin, stdout, stderr = ssh_client.exec_command(
                    'cat > /tmp/start_rtorrent_droplet.yml',
                    get_pty=True
                )
                stdin.write(playbook_content)
                stdin.channel.shutdown_write()
                stdout.read()  # Wait for completion
                ui_updater.add_text_to_output("✅ Playbook copied\n")
                
                # Run the playbook with the API key and SSH key name
                ui_updater.add_text_to_output("Running ansible-playbook...\n")
                command = (
                    f'export DIGITALOCEAN_TOKEN="{api_key}" && '
                    f'ansible-playbook /tmp/start_rtorrent_droplet.yml '
                    f'-e "ssh_key=briefcase_ansible"'
                )
                
                stdin, stdout, stderr = ssh_client.exec_command(command, get_pty=True)
                
                # Stream the output
                while True:
                    line = stdout.readline()
                    if not line:
                        break
                    ui_updater.add_text_to_output(line)
                
                # Check for errors
                error_output = stderr.read().decode()
                if error_output:
                    ui_updater.add_text_to_output(f"Errors:\n{error_output}\n")
                
                # Clean up the temporary file
                ssh_client.exec_command('rm -f /tmp/start_rtorrent_droplet.yml')
                
                # Close connection
                ssh_client.close()
                ui_updater.add_text_to_output("✅ SSH connection closed\n")
                ui_updater.add_text_to_output("✅ Droplet creation complete!\n")
                
            except Exception as e:
                ui_updater.add_text_to_output(f"❌ Droplet creation failed: {e}\n")
                import traceback
                ui_updater.add_text_to_output(f"Traceback:\n{traceback.format_exc()}\n")

        # Define button configurations as tuples: (label, callback, tooltip)
        button_configs = [
            (
                "Local Ansible Ping Test",
                lambda widget: ansible_ping_test(self, widget),
                "Run Ansible ping test",
            ),
            (
                "Test SSH Connection (ed25519)",
                lambda widget: self.background_task_runner.run_task(
                    lambda: test_ssh_connection(self.ui_updater),
                    "Testing SSH Connection with ed25519...",
                ),
                "Test SSH connection using ed25519 key",
            ),
            (
                "Generate Key (Cryptography)",
                lambda widget: self.background_task_runner.run_task(
                    lambda: generate_ed25519_key_cryptography(self.ui_updater),
                    "Generating ed25519 key with cryptography...",
                ),
                "Generate ed25519 SSH key using cryptography library",
            ),
            (
                "Test SSH Connection with Generated Key",
                lambda widget: self.background_task_runner.run_task(
                    lambda: test_ssh_connection_generated_key(self.ui_updater),
                    "Testing SSH Connection with generated key...",
                ),
                "Test SSH connection using the generated ed25519 key",
            ),
            (
                "Create rtorrent Droplet",
                lambda widget: self.background_task_runner.run_task(
                    lambda: run_droplet_playbook(self.ui_updater),
                    "Creating rtorrent droplet...",
                ),
                "Run the rtorrent droplet creation playbook from night2",
            ),
        ]

        # Create action buttons using UIComponents
        action_buttons = UIComponents.create_action_buttons(self, button_configs)

        # Create output area and status label
        self.output_view, self.status_label = UIComponents.create_output_area()

        # Create UI updater and background task runner with logger
        self.ui_updater = UIUpdater(
            self.output_view, self.status_label, self.main_event_loop, self.logger
        )
        self.background_task_runner = BackgroundTaskRunner(self.ui_updater)

        # Make sure background_task_runner uses our task set
        self.background_task_runner.background_tasks = self.background_tasks

        # Create main layout with all components
        main_box = UIComponents.create_main_layout(
            "Ansible Test Runner",
            action_buttons,
            self.output_view,
            self.status_label,
        )

        # Create and show the main window
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.size = (600, 400)
        self.main_window.show()

    def test_paramiko_connection(self, widget):
        """Test a basic Paramiko SSH connection."""

        # Run in background to keep UI responsive
        def run_in_background():
            # Get path to the SSH key
            key_path = os.path.join(
                self.paths.app, "resources", "keys", "briefcase_test_key"
            )
            # Run the SSH test with our UI updater and the key path
            test_ssh_connection(
                "night2", "mtm", key_path=key_path, ui_updater=self.ui_updater
            )

        # Run the task in a background thread
        self.background_task_runner.run_task(
            run_in_background, "Testing Paramiko connection..."
        )


def main():
    return BriefcaseAnsibleTest()
