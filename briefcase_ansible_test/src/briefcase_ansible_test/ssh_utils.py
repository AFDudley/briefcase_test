"""
SSH utilities for briefcase_ansible_test
"""

import os
import sys
import types
import inspect
from contextlib import contextmanager

import briefcase_ansible_test
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


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


def load_ssh_key(key_path: str):
    """
    Load an SSH private key from file, automatically detecting the key type.

    Args:
        key_path: Path to the private key file

    Returns:
        Loaded SSH key object

    Raises:
        FileNotFoundError: If key file doesn't exist
        paramiko.SSHException: If key cannot be loaded or type cannot be determined
    """
    paramiko = import_paramiko()

    # Verify key file exists
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"SSH key not found: {key_path}")

    # Try to load key with different types
    # The order matters - Ed25519 is most common in this codebase
    key_types = [
        (paramiko.Ed25519Key, "Ed25519"),
        (paramiko.RSAKey, "RSA"),
        (paramiko.ECDSAKey, "ECDSA"),
        (paramiko.DSSKey, "DSS"),
    ]

    last_error = None
    for key_class, key_name in key_types:
        try:
            return key_class.from_private_key_file(key_path)
        except paramiko.SSHException as e:
            last_error = e
            continue

    # If we get here, no key type worked
    raise paramiko.SSHException(
        f"Could not determine key type for {key_path}. Last error: {last_error}"
    )


@contextmanager
def ssh_client_context(hostname, username, port=22, pkey=None, timeout=5):
    """
    Context manager for SSH client connections with automatic cleanup.

    Args:
        hostname: The hostname to connect to
        username: The username to authenticate as
        port: The port to connect to (default: 22)
        pkey: SSH key object for authentication
        timeout: Connection timeout in seconds (default: 5)

    Yields:
        paramiko.SSHClient: Connected SSH client

    Raises:
        paramiko.AuthenticationException: If authentication fails
        paramiko.SSHException: If SSH connection fails
        Exception: For other connection errors
    """
    paramiko = import_paramiko()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect with the provided parameters
        client.connect(
            hostname=hostname,
            username=username,
            port=port,
            pkey=pkey,
            timeout=timeout,
            allow_agent=False,
            look_for_keys=False,
        )
        yield client
    finally:
        # Always close the client, even if an exception occurred
        client.close()


def execute_ssh_command(client, command, timeout=None):
    """
    Execute a command on an SSH client and return the result.

    Args:
        client: Connected paramiko SSHClient instance
        command: Command string to execute
        timeout: Optional timeout for command execution

    Returns:
        tuple: (success, stdout, stderr) where:
            - success: Boolean indicating if command succeeded (exit code 0)
            - stdout: String containing standard output
            - stderr: String containing standard error

    Raises:
        Exception: If command execution fails catastrophically
    """
    try:
        # Execute the command
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)

        # Read output and error streams
        stdout_data = stdout.read().decode("utf-8").strip()
        stderr_data = stderr.read().decode("utf-8").strip()

        # Get exit status
        exit_status = stdout.channel.recv_exit_status()

        # Success is determined by exit status
        success = exit_status == 0

        return success, stdout_data, stderr_data

    except Exception as e:
        # Return failure with exception information
        return False, "", str(e)


def test_ssh_connection(
    hostname="night2.lan", username="mtm", port=22, key_path=None, ui_updater=None
):
    """Test SSH connection using Paramiko with an ED25519 key."""
    ui = ui_updater.add_text_to_output if ui_updater else lambda x: None

    if not key_path:
        app_module_path = inspect.getfile(briefcase_ansible_test)
        app_dir = os.path.dirname(app_module_path)
        key_path = os.path.join(app_dir, "resources", "keys", "briefcase_test_key")

    key = load_ssh_key(key_path)
    ui(f"Testing SSH connection to {hostname}:{port} as {username}...\n")

    with ssh_client_context(hostname, username, port, pkey=key, timeout=5) as client:
        success, output, error = execute_ssh_command(client, "whoami")
        if success:
            ui(f"✅ SSH connection successful! Remote user: {output}\n")
            if ui_updater:
                ui_updater.update_status("Connected")
            return True
        else:
            ui(f"❌ SSH test command failed: {error}\n")
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
    """Generate a new ED25519 SSH key and save it to the app resources."""
    ui = ui_updater.add_text_to_output if ui_updater else lambda x: None

    ui("Generating ED25519 key pair...\n")
    ssh_dir = create_ssh_directory(app_path)

    # Generate and save private key
    private_key = ed25519.Ed25519PrivateKey.generate()
    private_key_openssh = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    )
    private_key_path = os.path.join(ssh_dir, "id_ed25519")
    with open(private_key_path, "wb") as f:
        f.write(private_key_openssh)

    # Generate and save public key
    pk = load_ssh_key(private_key_path)
    public_key_str = f"{pk.get_name()} {pk.get_base64()} ansible-briefcase-app"
    public_key_path = os.path.join(ssh_dir, "id_ed25519.pub")
    with open(public_key_path, "w") as f:
        f.write(public_key_str + "\n")

    ui(
        f"✅ Generated ED25519 key pair\n"
        f"Private: {private_key_path}\nPublic: {public_key_path}\n"
    )
    ui(f"Public Key:\n{public_key_str}\n")

    if ui_updater:
        ui_updater.update_status("Key Generated")
    return True, private_key_path, public_key_path, public_key_str


def test_ssh_connection_with_generated_key(app_paths, ui_updater):
    """Test SSH connection using generated ed25519 key."""
    ui = ui_updater.add_text_to_output
    ssh_dir = os.path.join(app_paths.app, "resources", "ssh")
    private_key_path = os.path.join(ssh_dir, "id_ed25519")
    public_key_path = os.path.join(ssh_dir, "id_ed25519.pub")

    if not os.path.exists(private_key_path):
        ui(
            "No generated key found. Please generate a key first using "
            "'Generate ED25519 Key' button.\n"
        )
        return

    with open(public_key_path, "r") as f:
        public_key_str = f.read().strip()
    ui(f"Using generated ed25519 public key:\n{public_key_str}\n")
    ui(
        "Make sure this key is added to ~/.ssh/authorized_keys for user "
        "'mtm' on night2.lan\n"
    )

    success = test_ssh_connection(
        "night2.lan", "mtm", key_path=private_key_path, ui_updater=ui_updater
    )
    ui(f"Generated key SSH connection test {'complete' if success else 'failed'}.\n")
