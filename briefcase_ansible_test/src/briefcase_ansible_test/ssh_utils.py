"""
SSH utilities for briefcase_ansible_test
"""

import os
import sys
import types
import traceback


def patch_paramiko_for_async():
    """
    Patch Paramiko 2.2.1 to work with Python 3.7+ by pre-empting problematic imports.

    This prevents the SyntaxError caused by the 'async' keyword in sftp_file.py
    by creating a dummy module before Paramiko tries to import it.

    Returns:
        bool: True if patch was applied, False otherwise
    """
    try:
        # Create dummy sftp_file module to prevent the real one from loading
        sftp_file_module = types.ModuleType("paramiko.sftp_file")

        # Add a dummy SFTPFile class with methods that don't use 'async' keyword
        class SFTPFile:

            def _close(self, async_=True):
                pass

            def close(self):
                pass

        # Add the class to the module - we need to use setattr for type checking
        setattr(sftp_file_module, "SFTPFile", SFTPFile)
        sys.modules["paramiko.sftp_file"] = sftp_file_module

        # Fix for MutableMapping in Python 3.10+
        if sys.version_info >= (3, 10):
            if "collections" in sys.modules:
                import collections
                from collections.abc import MutableMapping

                # Use hasattr check and setattr for type checking
                if not hasattr(collections, "MutableMapping"):
                    setattr(collections, "MutableMapping", MutableMapping)

        return True
    except Exception as e:
        print(f"Error patching Paramiko: {e}")
        return False


def import_paramiko():
    """
    Safely import Paramiko after applying necessary patches.

    Returns:
        The imported paramiko module

    Raises:
        ImportError: If Paramiko cannot be imported
    """
    # Apply patch first
    patched = patch_paramiko_for_async()
    if not patched:
        raise ImportError("Failed to apply Paramiko patches")

    # Import paramiko - let any exceptions propagate
    import paramiko

    return paramiko


def test_ssh_connection(hostname="night2.lan", username="mtm", port=22, key_path=None, ui_updater=None):
    """
    Test an SSH connection using Paramiko with an ED25519 key.

    Args:
        hostname: The hostname to connect to (default: "night2.lan")
        username: The username to authenticate as (default: "mtm")
        port: The port to connect to (default: 22)
        key_path: Path to private key file (default: looks for briefcase_test_key in resources/keys)
        ui_updater: UI updater for showing progress (optional)

    Returns:
        bool: True if connection test was successful, False otherwise
    """
    try:
        paramiko = import_paramiko()
    except ImportError as e:
        if ui_updater:
            ui_updater.add_text_to_output(f"Failed to import Paramiko: {str(e)}\n")
            ui_updater.update_status("Failed")
        return False

    if ui_updater:
        paramiko_version = getattr(paramiko, "__version__", "unknown")
        ui_updater.add_text_to_output(f"Paramiko version: {paramiko_version}\n")
        ui_updater.add_text_to_output("Initializing SSH client...\n")

    try:
        # Create client instance
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Use default key path if none provided
        if not key_path:
            # Try to find the app directory and default key
            try:
                import briefcase_ansible_test
                import inspect
                app_module_path = inspect.getfile(briefcase_ansible_test)
                app_dir = os.path.dirname(app_module_path)
                key_path = os.path.join(app_dir, "resources", "keys", "briefcase_test_key")
                if ui_updater:
                    ui_updater.add_text_to_output(f"Using default key path: {key_path}\n")
            except Exception as e:
                if ui_updater:
                    ui_updater.add_text_to_output(f"❌ Could not determine default key path: {e}\n")
                return False

        # Check if key exists
        key = None

        if os.path.exists(key_path):
            if ui_updater:
                ui_updater.add_text_to_output(f"Using key: {key_path}\n")

            # Set proper permissions
            try:
                os.chmod(key_path, 0o600)
            except Exception as e:
                if ui_updater:
                    ui_updater.add_text_to_output(
                        f"Warning: Could not set key permissions: {str(e)}\n"
                    )

            # Try to load as ED25519 key
            try:
                key = paramiko.Ed25519Key.from_private_key_file(key_path)
                if ui_updater:
                    ui_updater.add_text_to_output(
                        "✅ Successfully loaded ED25519 key\n"
                    )
            except Exception as e:
                if ui_updater:
                    ui_updater.add_text_to_output(
                        f"❌ Error loading ED25519 key: {str(e)}\n"
                    )
        elif ui_updater:
            ui_updater.add_text_to_output(f"❌ No key found at: {key_path}\n")

        # Attempt connection
        if ui_updater:
            ui_updater.add_text_to_output(
                f"Connecting to {hostname}:{port} as {username}...\n"
            )

        # Connect with a timeout
        client.connect(
            hostname=hostname,
            username=username,
            port=port,
            pkey=key,
            timeout=5,
            allow_agent=False,
            look_for_keys=False,
        )

        if ui_updater:
            ui_updater.add_text_to_output("✅ Connection successful!\n")

        # Test a simple command if connected
        stdin, stdout, stderr = client.exec_command("echo Hello from Paramiko")
        output = stdout.read().decode("utf-8").strip()

        if ui_updater:
            ui_updater.add_text_to_output(f"Command output: {output}\n")

        # Close connection
        client.close()

        if ui_updater:
            ui_updater.update_status("Connected")
        return True

    except paramiko.AuthenticationException as e:
        if ui_updater:
            ui_updater.add_text_to_output(f"❌ Authentication failed: {str(e)}\n")
            ui_updater.add_text_to_output("💡 Check that the public key is added to ~/.ssh/authorized_keys on the server\n")
            ui_updater.update_status("Auth Failed")
        return False

    except paramiko.SSHException as e:
        if ui_updater:
            ui_updater.add_text_to_output(f"❌ SSH error: {str(e)}\n")
            ui_updater.update_status("SSH Failed")
        return False

    except Exception as e:
        if ui_updater:
            ui_updater.add_text_to_output(f"Error: {str(e)}\n")
            ui_updater.add_text_to_output(f"Traceback: {traceback.format_exc()}\n")
            ui_updater.update_status("Error")
        return False


def create_ssh_directory(app_path):
    """
    Create a directory for SSH keys if it doesn't exist.

    Args:
        app_path: The application path to use as base directory

    Returns:
        str: Path to the SSH directory
    """
    ssh_dir = os.path.join(app_path, "resources", "ssh")
    if not os.path.exists(ssh_dir):
        os.makedirs(ssh_dir, exist_ok=True)
    return ssh_dir


def generate_ed25519_key(app_path, ui_updater=None):
    """
    Generate a new ED25519 SSH key and save it to the app resources.

    Args:
        app_path: The application path to use as base directory
        ui_updater: Optional UI updater for showing progress

    Returns:
        tuple: (success, private_key_path, public_key_path, public_key_str)
    """
    try:
        from cryptography.hazmat.primitives.asymmetric import ed25519
        from cryptography.hazmat.primitives import serialization
        import paramiko

        if ui_updater:
            ui_updater.add_text_to_output("Generating new ED25519 key pair...\n")

        # Create the SSH directory
        ssh_dir = create_ssh_directory(app_path)

        # Generate a new ED25519 private key
        private_key = ed25519.Ed25519PrivateKey.generate()

        # Get the public key (used to create the public key file)
        private_key.public_key()

        # Serialize the private key to OpenSSH format for file storage
        private_key_openssh = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.OpenSSH,
            encryption_algorithm=serialization.NoEncryption(),
        )

        # Save the private key
        private_key_path = os.path.join(ssh_dir, "id_ed25519")
        with open(private_key_path, "wb") as f:
            f.write(private_key_openssh)

        # Make sure permissions are set correctly (600)
        os.chmod(private_key_path, 0o600)

        # Create the public key in OpenSSH format
        # Use paramiko to load the key and get the proper format
        pk = paramiko.Ed25519Key.from_private_key_file(private_key_path)
        public_key_str = f"{pk.get_name()} {pk.get_base64()} ansible-briefcase-app"

        # Save the public key
        public_key_path = os.path.join(ssh_dir, "id_ed25519.pub")
        with open(public_key_path, "w") as f:
            f.write(public_key_str)
            f.write("\n")

        # Display information if ui_updater is provided
        if ui_updater:
            ui_updater.add_text_to_output("Generated ED25519 key pair:\n")
            ui_updater.add_text_to_output(f"Private key: {private_key_path}\n")
            ui_updater.add_text_to_output(f"Public key: {public_key_path}\n\n")

            ui_updater.add_text_to_output(
                "Public Key (add this to authorized_keys on your server):\n"
            )
            ui_updater.add_text_to_output(f"{public_key_str}\n\n")

            # Display fingerprint
            fingerprint = pk.get_fingerprint().hex()
            # Format fingerprint with colons between each byte
            chunks = [fingerprint[i : i + 2] for i in range(0, len(fingerprint), 2)]
            formatted_fp = ":".join(chunks)
            ui_updater.add_text_to_output(f"Key Fingerprint: {formatted_fp}\n")
            ui_updater.update_status("Key Generated")

        return True, private_key_path, public_key_path, public_key_str

    except ImportError as e:
        if ui_updater:
            ui_updater.add_text_to_output(
                f"Error importing required modules: {str(e)}\n"
            )
            ui_updater.add_text_to_output(
                "Make sure 'cryptography' and 'paramiko' are installed.\n"
            )
            ui_updater.update_status("Failed")
        return False, None, None, None


def test_ssh_connection_with_generated_key(app_paths, ui_updater):
    """Test SSH connection using generated ed25519 key"""
    try:
        ui_updater.add_text_to_output("Testing SSH Connection with generated key...\n")
        
        # Check if generated key exists
        ssh_dir = os.path.join(app_paths.app, "resources", "ssh")
        private_key_path = os.path.join(ssh_dir, "id_ed25519")
        public_key_path = os.path.join(ssh_dir, "id_ed25519.pub")
        
        if not os.path.exists(private_key_path):
            ui_updater.add_text_to_output("❌ No generated key found. Please generate a key first using 'Generate ED25519 Key' button.\n")
            return
        
        # Display the public key
        try:
            with open(public_key_path, 'r') as f:
                public_key_str = f.read().strip()
            ui_updater.add_text_to_output(f"📋 Using generated ed25519 public key:\n{public_key_str}\n")
            ui_updater.add_text_to_output("💡 Make sure this key is added to ~/.ssh/authorized_keys for user 'mtm' on night2.lan\n")
        except Exception as e:
            ui_updater.add_text_to_output(f"⚠ Could not read public key: {e}\n")
        
        # Test SSH connection using the existing test_ssh_connection function
        ui_updater.add_text_to_output("🔧 Testing SSH connection with generated key...\n")
        success = test_ssh_connection("night2.lan", "mtm", key_path=private_key_path, ui_updater=ui_updater)
        
        if success:
            ui_updater.add_text_to_output("✅ Generated key SSH connection test complete.\n")
        else:
            ui_updater.add_text_to_output("❌ Generated key SSH connection test failed.\n")
        
    except Exception as e:
        ui_updater.add_text_to_output(f"❌ Generated key SSH connection failed: {e}\n")
        import traceback
        ui_updater.add_text_to_output(f"Traceback:\n{traceback.format_exc()}\n")
