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
        sys.modules['paramiko.sftp_file'] = types.ModuleType('paramiko.sftp_file')
        
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
    Test an SSH connection using Paramiko.
    
    Args:
        hostname: The hostname to connect to
        username: The username to authenticate as
        port: The port to connect to (default: 22)
        key_path: Path to private key file (optional)
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
        
        # Check if key exists
        key = None
        if key_path and os.path.exists(key_path):
            if ui_updater:
                ui_updater.add_text_to_output(f"Using key: {key_path}\n")
            try:
                key = paramiko.RSAKey.from_private_key_file(key_path)
                if ui_updater:
                    ui_updater.add_text_to_output("Successfully loaded key\n")
            except Exception as e:
                if ui_updater:
                    ui_updater.add_text_to_output(f"Error loading key: {str(e)}\n")
        
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
            ui_updater.add_text_to_output("Connection successful!\n")
        
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

def generate_ssh_key(key_path, key_type="rsa", bits=2048, ui_updater=None):
    """
    Generate an SSH key pair.
    
    Args:
        key_path: Path to save the private key (public key will be key_path + '.pub')
        key_type: Key type, either 'rsa' or 'ed25519' (default: 'rsa')
        bits: Key size in bits for RSA keys (default: 2048)
        ui_updater: UI updater for showing progress (optional)
    
    Returns:
        bool: True if key generation was successful, False otherwise
    """
    success, paramiko = import_paramiko()
    if not success:
        if ui_updater:
            ui_updater.add_text_to_output("Failed to import Paramiko\n")
            ui_updater.update_status("Failed")
        return False
    
    if ui_updater:
        ui_updater.add_text_to_output(f"Generating {key_type.upper()} SSH key...\n")
    
    # Create directory if it doesn't exist
    key_dir = os.path.dirname(key_path)
    if not os.path.exists(key_dir):
        os.makedirs(key_dir, exist_ok=True)
    
    try:
        # Generate key based on type
        if key_type.lower() == "ed25519":
            try:
                # Try to use Ed25519 if available
                key = paramiko.Ed25519Key.generate()
                if ui_updater:
                    ui_updater.add_text_to_output("Generated ED25519 key\n")
            except (AttributeError, ImportError):
                # Fall back to RSA if Ed25519 not available
                key = paramiko.RSAKey.generate(bits=bits)
                if ui_updater:
                    ui_updater.add_text_to_output("ED25519 not supported, fell back to RSA\n")
        else:
            # Generate RSA key
            key = paramiko.RSAKey.generate(bits=bits)
            if ui_updater:
                ui_updater.add_text_to_output(f"Generated {bits}-bit RSA key\n")
        
        # Save private key
        key.write_private_key_file(key_path)
        os.chmod(key_path, 0o600)  # Set appropriate permissions
        
        # Generate and save public key
        pub_key_path = key_path + '.pub'
        with open(pub_key_path, 'w') as f:
            f.write(f"{key.get_name()} {key.get_base64()} generated-key\n")
        
        if ui_updater:
            ui_updater.add_text_to_output(f"Private key saved to: {key_path}\n")
            ui_updater.add_text_to_output(f"Public key saved to: {pub_key_path}\n")
            
            # Read and display public key
            with open(pub_key_path, 'r') as f:
                pub_key = f.read().strip()
                ui_updater.add_text_to_output(f"\nPublic key (add to authorized_keys):\n{pub_key}\n")
            
            ui_updater.update_status("Key Generated")
        
        return True
        
    except Exception as e:
        if ui_updater:
            ui_updater.add_text_to_output(f"Error generating key: {str(e)}\n")
            ui_updater.add_text_to_output(f"Traceback: {traceback.format_exc()}\n")
            ui_updater.update_status("Failed")
        return False