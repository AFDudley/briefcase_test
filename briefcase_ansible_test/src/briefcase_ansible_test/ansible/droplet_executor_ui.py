"""
UI wrapper for droplet operations.
"""

import os
from typing import Optional, Callable
from .droplet_executor import (
    create_droplet,
    create_droplet_with_ephemeral_key,
    cleanup_droplet_resources,
    DropletExecutionResult,
)


def run_droplet_playbook_ui(
    playbook_path: str,
    inventory_path: str,
    api_key_path: str,
    ui_updater,
    ssh_key_name: str = "briefcase_ansible",
    timeout: int = 300,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> bool:
    """UI-aware wrapper for droplet creation."""
    try:
        # Progress notification
        if progress_callback:
            progress_callback("Starting droplet creation...")

        ui_updater.add_text_to_output("🚀 Starting rtorrent droplet creation...\n")

        # Call pure business logic
        result = create_droplet(
            playbook_path=playbook_path,
            inventory_path=inventory_path,
            api_key_path=api_key_path,
            ssh_key_name=ssh_key_name,
            timeout=timeout,
        )

        # Update UI with messages
        for message in result.messages:
            ui_updater.add_text_to_output(f"📋 {message}\n")

        if result.success:
            ui_updater.add_text_to_output(
                f"✅ Droplet created successfully\n"
                f"   ID: {result.droplet_id}\n"
                f"   IP: {result.droplet_ip}\n"
            )
            if progress_callback:
                progress_callback("Droplet created successfully")
        else:
            ui_updater.add_text_to_output(f"❌ {result.error}\n")
            if progress_callback:
                progress_callback("Droplet creation failed")

        return result.success

    except Exception:
        # Let errors propagate - no hiding
        raise


def run_droplet_playbook_ui_ephemeral(
    playbook_path: str,
    inventory_path: str,
    api_key_path: str,
    ssh_keys_dir: str,
    ui_updater,
    timeout: int = 300,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> DropletExecutionResult:
    """Create droplet with ephemeral SSH key - returns full result."""
    try:
        # Progress notification
        if progress_callback:
            progress_callback("Generating ephemeral SSH key...")

        ui_updater.add_text_to_output("🚀 Creating droplet with ephemeral SSH key...\n")

        # Call pure business logic
        result = create_droplet_with_ephemeral_key(
            playbook_path=playbook_path,
            inventory_path=inventory_path,
            api_key_path=api_key_path,
            ssh_keys_dir=ssh_keys_dir,
            timeout=timeout,
        )

        # Update UI with messages
        for message in result.messages:
            ui_updater.add_text_to_output(f"📋 {message}\n")

        if result.success:
            ui_updater.add_text_to_output(
                f"✅ Droplet created with ephemeral key\n"
                f"   ID: {result.droplet_id}\n"
                f"   IP: {result.droplet_ip}\n"
                f"   SSH Key: {result.ssh_key_name}\n"
            )
            if progress_callback:
                progress_callback("Droplet created successfully")
        else:
            ui_updater.add_text_to_output(f"❌ {result.error}\n")
            if progress_callback:
                progress_callback("Droplet creation failed")

        return result

    except Exception:
        # Let errors propagate
        raise


def cleanup_droplet_ui(
    cleanup_playbook_path: str,
    inventory_path: str,
    api_key_path: str,
    droplet_name: str,
    ssh_key_name: str,
    ui_updater,
    timeout: int = 60,
) -> bool:
    """UI wrapper for droplet cleanup."""
    try:
        ui_updater.add_text_to_output(
            f"🧹 Cleaning up droplet {droplet_name} and SSH key {ssh_key_name}...\n"
        )

        result = cleanup_droplet_resources(
            cleanup_playbook_path=cleanup_playbook_path,
            inventory_path=inventory_path,
            api_key_path=api_key_path,
            droplet_name=droplet_name,
            ssh_key_name=ssh_key_name,
            timeout=timeout,
        )

        # Update UI with messages
        for message in result.messages:
            ui_updater.add_text_to_output(f"📋 {message}\n")

        if result.success:
            ui_updater.add_text_to_output("✅ Cleanup completed successfully\n")
        else:
            ui_updater.add_text_to_output(f"❌ Cleanup failed: {result.error}\n")

        return result.success

    except Exception:
        # Let errors propagate
        raise


# Backwards compatibility function for app.py
def run_droplet_playbook(app_paths, ui_updater):
    """Legacy UI wrapper for droplet creation."""
    # Build paths
    api_key_file = os.path.join(app_paths.app, "resources", "api_keys", "do.api_key")
    inventory_file = os.path.join(
        app_paths.app, "resources", "inventory", "sample_inventory.ini"
    )
    playbook_file = os.path.join(
        app_paths.app, "resources", "playbooks", "start_rtorrent_droplet.yml"
    )

    # Use new UI wrapper
    return run_droplet_playbook_ui(
        playbook_path=playbook_file,
        inventory_path=inventory_file,
        api_key_path=api_key_file,
        ui_updater=ui_updater,
        timeout=300,
    )
