"""
Test direct SSH connection to 127.0.0.1.

This test verifies that SSH connections work properly and report errors correctly.
"""

import os


def test_ssh_connection(ui_updater):
    """Test direct SSH connection to host from inventory"""
    ui_updater.add_text_to_output("Testing SSH Connection from inventory...\n")

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

    # Import ansible module to trigger patches
    import briefcase_ansible_test.ansible

    # Parse inventory to get hosts
    from ansible.parsing.dataloader import DataLoader
    from ansible.inventory.manager import InventoryManager

    # Get inventory path
    import briefcase_ansible_test
    import inspect

    # Use inspect to get the module path
    app_module_path = inspect.getfile(briefcase_ansible_test)
    app_dir = os.path.dirname(app_module_path)
    inventory_path = os.path.join(
        app_dir, "resources", "inventory", "sample_inventory.ini"
    )

    ui_updater.add_text_to_output(f"📁 Reading inventory: {inventory_path}\n")

    # Load inventory
    loader = DataLoader()
    inventory = InventoryManager(loader=loader, sources=[inventory_path])

    # Get hosts from the "night2" group
    night2_hosts = inventory.get_hosts("night2")
    ui_updater.add_text_to_output(
        f"Found {len(night2_hosts)} hosts in 'night2' group\n"
    )

    # Use the first host from night2 group
    target_host = night2_hosts[0]
    ui_updater.add_text_to_output(
        f"✅ Selected host from night2 group: {target_host.name}\n"
    )

    # Show host variables if any
    host_vars = target_host.get_vars()
    if host_vars:
        ui_updater.add_text_to_output("Host variables:\n")
        for key, value in host_vars.items():
            if not key.startswith("ansible_") or key in [
                "ansible_host",
                "ansible_user",
                "ansible_port",
            ]:
                ui_updater.add_text_to_output(f"  {key}: {value}\n")

    # Get SSH key path
    key_path = os.path.join(app_dir, "resources", "keys", "briefcase_test_key")

    ui_updater.add_text_to_output(f"📁 SSH key path: {key_path}\n")

    # Check if key exists
    if os.path.exists(key_path):
        ui_updater.add_text_to_output("✅ SSH key found\n")

        # Also check for public key
        pub_key_path = key_path + ".pub"
        if os.path.exists(pub_key_path):
            ui_updater.add_text_to_output(f"✅ SSH public key found: {pub_key_path}\n")
            with open(pub_key_path, "r") as f:
                pub_key_content = f.read().strip()
            ui_updater.add_text_to_output(
                f"📋 Ed25519 Public key:\n{pub_key_content}\n"
            )

            # Check if it's actually an Ed25519 key
            if pub_key_content.startswith("ssh-ed25519"):
                ui_updater.add_text_to_output("✅ Key is in Ed25519 format\n")
            else:
                ui_updater.add_text_to_output(
                    "⚠️ Key does not appear to be Ed25519 format\n"
                )
                ui_updater.add_text_to_output(
                    "   Expected to start with 'ssh-ed25519'\n"
                )

            ui_updater.add_text_to_output(
                "\n💡 To authorize this key, add it to ~/.ssh/authorized_keys for user 'mtm'\n"
            )
        else:
            ui_updater.add_text_to_output("⚠️ No public key file found\n")
    else:
        ui_updater.add_text_to_output("❌ SSH key not found\n")
        return

    # Test with Paramiko directly
    ui_updater.add_text_to_output("\n🔧 Testing Paramiko SSH connection...\n")

    import paramiko

    ui_updater.add_text_to_output("✅ Paramiko imported\n")

    # Create SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ui_updater.add_text_to_output("✅ SSH client created\n")

    # Enable debug logging for more details (util module might not exist)
    if hasattr(paramiko, 'util'):
        paramiko.util.log_to_file("/dev/stdout")

    # Try to connect
    ui_updater.add_text_to_output(
        f"🚀 Attempting SSH connection to {target_host.name}...\n"
    )
    ui_updater.add_text_to_output(f"   User: mtm\n")
    ui_updater.add_text_to_output(f"   Key: {key_path}\n")

    # Load the Ed25519 key
    private_key = paramiko.Ed25519Key.from_private_key_file(key_path)
    ui_updater.add_text_to_output("✅ SSH Ed25519 private key loaded successfully\n")

    # Connect - let any errors bubble up
    ssh.connect(
        hostname=target_host.name,
        username="mtm",
        pkey=private_key,  # Use loaded Ed25519 key
        timeout=10,
        look_for_keys=False,
        allow_agent=False,
    )

    ui_updater.add_text_to_output("✅ SSH connection successful!\n")

    # Try to run a command
    ui_updater.add_text_to_output("\n📋 Testing command execution...\n")
    stdin, stdout, stderr = ssh.exec_command('echo "Hello from SSH"')

    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()

    ui_updater.add_text_to_output(f"Command output: {output}\n")
    if error:
        ui_updater.add_text_to_output(f"Command error: {error}\n")

    ui_updater.add_text_to_output("✅ Command execution successful!\n")

    # Close connection
    ssh.close()
    ui_updater.add_text_to_output("✅ SSH connection closed\n")

    ui_updater.add_text_to_output("\n✅ SSH connection test complete.\n")
