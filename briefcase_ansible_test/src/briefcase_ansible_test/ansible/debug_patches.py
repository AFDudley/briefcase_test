"""
Debug patches for Ansible on iOS.

This module provides debug patches for WorkerProcess and connection plugins.
"""


def apply_worker_debug_patches(output_callback):
    """
    Apply debugging patches to Ansible WorkerProcess.
    
    Args:
        output_callback: Function to call with output messages
        
    Returns:
        bool: True if successful, False otherwise
    """
    output_callback("Patching WorkerProcess for debugging...\n")
    try:
        from briefcase_ansible_test.ansible_worker_debug import (
            patch_worker_process_for_debugging,
        )

        if patch_worker_process_for_debugging():
            output_callback("✅ WorkerProcess patched\n")
            return True
        else:
            output_callback("⚠️ WorkerProcess patch failed\n")
            return False
    except Exception as e:
        output_callback(f"❌ WorkerProcess patch error: {e}\n")
        return False


def apply_connection_debug_patches(output_callback):
    """
    Apply debugging patches to Ansible connection plugins.
    
    Args:
        output_callback: Function to call with output messages
        
    Returns:
        bool: True if successful, False otherwise
    """
    output_callback("Patching connection plugins...\n")
    try:
        from briefcase_ansible_test.ansible_connection_debug import (
            patch_connection_plugins,
        )

        if patch_connection_plugins():
            output_callback("✅ Connection plugins patched\n")
            return True
        else:
            output_callback("⚠️ Connection plugin patch failed\n")
            return False
    except Exception as e:
        output_callback(f"❌ Connection plugin patch error: {e}\n")
        return False


def verify_ping_module(output_callback):
    """
    Verify that the Ansible ping module is available.
    
    Args:
        output_callback: Function to call with output messages
        
    Returns:
        bool: True if available, False otherwise
    """
    try:
        from ansible.modules.ping import main as ping_main
        output_callback("✅ Ping module available\n")
        return True
    except ImportError as e:
        output_callback(f"❌ Ping module not available: {e}\n")
        return False