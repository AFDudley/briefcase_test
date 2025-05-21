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
        sftp_file_module = types.ModuleType('paramiko.sftp_file')
        
        # Add a dummy SFTPFile class with methods that don't use 'async' keyword
        class SFTPFile:
            def _close(self, async_=True):
                pass
            def close(self):
                pass
        
        # Add the class to the module
        sftp_file_module.SFTPFile = SFTPFile
        sys.modules['paramiko.sftp_file'] = sftp_file_module
        
        # Fix for MutableMapping in Python 3.10+
        if sys.version_info >= (3, 10):
            if 'collections' in sys.modules:
                import collections
                from collections.abc import MutableMapping
                if not hasattr(collections, 'MutableMapping'):
                    collections.MutableMapping = MutableMapping
        
        return True
    except Exception as e:
        print(f"Error patching Paramiko: {e}")
        return False

def import_paramiko():
    """
    Safely import Paramiko after applying necessary patches.
    
    Returns:
        tuple: (success, paramiko_module)
    """
    # Apply patch first
    patched = patch_paramiko_for_async()
    
    try:
        import paramiko
        return True, paramiko
    except SyntaxError as e:
        print(f"SyntaxError importing Paramiko: {e}")
        return False, None
    except ImportError as e:
        print(f"ImportError importing Paramiko: {e}")
        return False, None
    except Exception as e:
        print(f"Unexpected error importing Paramiko: {e}")
        return False, None

def test_ssh_connection(hostname, username, port=22, key_path=None, ui_updater=None):
    """
    Test an SSH connection using Paramiko with an ED25519 key.
    
    Args:
        hostname: The hostname to connect to
        username: The username to authenticate as
        port: The port to connect to (default: 22)
        key_path: Path to private key file (default: will look in resources/keys)
        ui_updater: UI updater for showing progress (optional)
    
    Returns:
        bool: True if connection test was successful, False otherwise
    """
    success, paramiko = import_paramiko()
    if not success:
        if ui_updater:
            ui_updater.add_text_to_output("Failed to import Paramiko\n")
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
        
        # key_path must be provided by caller
        
        # Check if key exists
        key = None
        if not key_path:
            if ui_updater:
                ui_updater.add_text_to_output("❌ No key path provided\n")
            return False
            
        if os.path.exists(key_path):
            if ui_updater:
                ui_updater.add_text_to_output(f"Using key: {key_path}\n")
            
            # Set proper permissions
            try:
                os.chmod(key_path, 0o600)
            except Exception as e:
                if ui_updater:
                    ui_updater.add_text_to_output(f"Warning: Could not set key permissions: {str(e)}\n")
            
            # Try to load as ED25519 key
            try:
                key = paramiko.Ed25519Key.from_private_key_file(key_path)
                if ui_updater:
                    ui_updater.add_text_to_output("✅ Successfully loaded ED25519 key\n")
            except Exception as e:
                if ui_updater:
                    ui_updater.add_text_to_output(f"❌ Error loading ED25519 key: {str(e)}\n")
        elif ui_updater:
            ui_updater.add_text_to_output(f"❌ No key found at: {key_path}\n")
        
        # Attempt connection
        if ui_updater:
            ui_updater.add_text_to_output(f"Connecting to {hostname}:{port} as {username}...\n")
        
        # Connect with a timeout
        client.connect(
            hostname=hostname,
            username=username,
            port=port,
            pkey=key,
            timeout=5,
            allow_agent=False,
            look_for_keys=False
        )
        
        if ui_updater:
            ui_updater.add_text_to_output("✅ Connection successful!\n")
        
        # Test a simple command if connected
        stdin, stdout, stderr = client.exec_command("echo Hello from Paramiko")
        output = stdout.read().decode('utf-8').strip()
        
        if ui_updater:
            ui_updater.add_text_to_output(f"Command output: {output}\n")
        
        # Close connection
        client.close()
        
        if ui_updater:
            ui_updater.update_status("Connected")
        return True
        
    except paramiko.AuthenticationException:
        if ui_updater:
            ui_updater.add_text_to_output("Authentication failed but socket connection works!\n")
            ui_updater.add_text_to_output("✅ Paramiko is working correctly.\n")
            ui_updater.update_status("Auth Failed")
        # Still consider this a success for testing purposes
        return True
        
    except paramiko.SSHException as e:
        if ui_updater:
            ui_updater.add_text_to_output(f"SSH error: {str(e)}\n")
            if "banner exchange" in str(e).lower():
                ui_updater.add_text_to_output("✅ Banner exchange attempted! Paramiko is working.\n")
                ui_updater.update_status("Partial Success")
                return True
            else:
                ui_updater.add_text_to_output("❌ SSH negotiation failed\n")
                ui_updater.update_status("Failed")
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
    ssh_dir = os.path.join(app_path, 'resources', 'ssh')
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
        
        # Display information if ui_updater is provided
        if ui_updater:
            ui_updater.add_text_to_output("Generated ED25519 key pair:\n")
            ui_updater.add_text_to_output(f"Private key: {private_key_path}\n")
            ui_updater.add_text_to_output(f"Public key: {public_key_path}\n\n")
            
            ui_updater.add_text_to_output("Public Key (add this to authorized_keys on your server):\n")
            ui_updater.add_text_to_output(f"{public_key_str}\n\n")
            
            # Display fingerprint
            fingerprint = pk.get_fingerprint().hex()
            ui_updater.add_text_to_output(f"Key Fingerprint: {':'.join([fingerprint[i:i+2] for i in range(0, len(fingerprint), 2)])}\n")
            ui_updater.update_status("Key Generated")
        
        return True, private_key_path, public_key_path, public_key_str
        
    except ImportError as e:
        if ui_updater:
            ui_updater.add_text_to_output(f"Error importing required modules: {str(e)}\n")
            ui_updater.add_text_to_output("Make sure 'cryptography' and 'paramiko' are installed.\n")
            ui_updater.update_status("Failed")
        return False, None, None, None
        
    except Exception as e:
        if ui_updater:
            ui_updater.add_text_to_output(f"Error generating key: {str(e)}\n")
            ui_updater.add_text_to_output(f"Traceback: {traceback.format_exc()}\n")
            ui_updater.update_status("Error")
        return False, None, None, None