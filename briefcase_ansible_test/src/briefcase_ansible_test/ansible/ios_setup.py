"""
iOS-specific setup utilities for Ansible.

This module provides functions to set up Ansible for iOS compatibility,
including directory access checks and temporary directory configuration.
"""

import os
import tempfile
import ansible.constants


def check_multiprocessing_availability(output_callback):
    """
    Check availability of multiprocessing modules.

    Args:
        output_callback: Function to call with output messages
    """
    output_callback("Checking multiprocessing availability...\n")
    multiprocessing_modules = [
        "multiprocessing",
        "multiprocessing.synchronize",
    ]
    for module_name in multiprocessing_modules:
        try:
            import importlib

            module = importlib.import_module(module_name)
            output_callback(f"✅ {module_name} is available\n")
            if module_name == "multiprocessing":
                output_callback(
                    f"   Process class: {getattr(module, 'Process', 'Not found')}\n"
                )
        except ImportError as e:
            output_callback(f"❌ {module_name} not available: {e}\n")


def find_writable_directory(app):
    """
    Find a writable directory for Ansible operations.

    Args:
        app: The application instance

    Returns:
        tuple: (writable_dir, test_results) where test_results is a list
               of (dir, success, error) tuples
    """
    test_results = []
    home_dir = os.path.expanduser("~")

    # Test write access to different directories
    test_dirs = [
        home_dir,
        os.path.join(home_dir, ".ansible"),
        tempfile.gettempdir(),
        (
            app.paths.cache
            if hasattr(app, "paths") and hasattr(app.paths, "cache")
            else None
        ),
        (
            app.paths.data
            if hasattr(app, "paths") and hasattr(app.paths, "data")
            else None
        ),
    ]

    writable_dir = None
    for test_dir in test_dirs:
        if test_dir is None:
            continue
        try:
            os.makedirs(test_dir, exist_ok=True)
            # Test write access
            test_file = os.path.join(test_dir, "test_write_access")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            test_results.append((test_dir, True, None))
            if writable_dir is None:
                writable_dir = test_dir
        except Exception as e:
            test_results.append((test_dir, False, str(e)))

    return writable_dir, test_results


def setup_ansible_temp_directory(writable_dir, output_callback):
    """
    Set up Ansible temporary directory in a writable location.

    Args:
        writable_dir: Path to a writable directory
        output_callback: Function to call with output messages

    Returns:
        bool: True if successful, False otherwise
    """
    if not writable_dir:
        output_callback("❌ No writable directory provided!\n")
        return False

    ansible_tmp_dir = os.path.join(writable_dir, ".ansible", "tmp")
    output_callback(f"Using Ansible temp directory: {ansible_tmp_dir}\n")

    try:
        os.makedirs(ansible_tmp_dir, exist_ok=True)

        # Configure Ansible to use our writable directory
        # Set the temporary directory paths (these constants might not exist)
        if hasattr(ansible.constants, "DEFAULT_LOCAL_TMP"):
            setattr(ansible.constants, "DEFAULT_LOCAL_TMP", ansible_tmp_dir)
        if hasattr(ansible.constants, "DEFAULT_REMOTE_TMP"):
            setattr(ansible.constants, "DEFAULT_REMOTE_TMP", ansible_tmp_dir)

        # Also set environment variables as fallback
        os.environ["ANSIBLE_LOCAL_TEMP"] = ansible_tmp_dir
        os.environ["ANSIBLE_REMOTE_TEMP"] = ansible_tmp_dir
        os.environ["TMPDIR"] = writable_dir  # Set system temp dir

        output_callback("✅ Ansible temp directory configured\n")
        return True
    except Exception as e:
        output_callback(f"❌ Failed to create temp directory: {e}\n")
        return False
