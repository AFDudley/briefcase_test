"""
Ansible utilities for briefcase_ansible_test

This module contains Ansible-related functionality for iOS-compatible operations.
"""

import sys
import types
import os
import stat

# Ensure system mocks are set up before importing anything else
from briefcase_ansible_test.utils.system_utils import (
    patch_getpass,
    setup_pwd_module_mock,
    setup_grp_module_mock,
)

# Import SSH utilities for Paramiko patching
from briefcase_ansible_test.ssh_utils import patch_paramiko_for_async

# Apply patch for Paramiko's async keyword issue - needed before Ansible imports
# that might indirectly use Paramiko for SSH connections
patch_paramiko_for_async()

# Define functions needed for Ansible mocks


def is_executable(path):
    """
    Check if a file is executable, with cross-platform compatibility.

    This implementation works on platforms like iOS where traditional
    executable permissions might not behave as expected.

    Args:
        path (str): The path to the file to check.

    Returns:
        bool: True if the file appears to be executable, False otherwise.
    """
    # Check if the file exists
    if not os.path.exists(path):
        return False

    # Get the file mode
    file_mode = os.stat(path).st_mode

    # Check for executable permission or executable file extension
    return (file_mode & stat.S_IXUSR) or path.endswith((".sh", ".py", ".bin", ".exe"))


# Define our own text module mock
def setup_ansible_text_module_mock():
    """
    Install a mock for ansible.module_utils._text in sys.modules.

    This provides text conversion utilities that Ansible needs.
    """

    class TextModuleType(types.ModuleType):
        def __init__(self):
            super().__init__("ansible.module_utils._text")
            self.to_native = lambda x, errors="strict": str(x)
            self.to_bytes = lambda obj, encoding="utf-8", errors="strict": (
                obj.encode(encoding, errors) if isinstance(obj, str) else obj
            )
            self.to_text = lambda obj, encoding="utf-8", errors="strict": (
                obj.decode(encoding, errors) if isinstance(obj, bytes) else str(obj)
            )

    sys.modules["ansible.module_utils._text"] = TextModuleType()


# Define our own basic module mock
def setup_ansible_basic_module_mock():
    """
    Patch ansible.module_utils.basic to use our is_executable implementation.

    This should be called after importing ansible but before using any modules
    that might depend on the patched functionality.
    """
    try:
        # Import the real module to use most of its functionality
        import ansible.module_utils.basic as real_basic

        # Create a new module using ModuleType
        class BasicModuleType(types.ModuleType):
            def __init__(self):
                super().__init__("ansible.module_utils.basic")
                # Copy all attributes from real_basic
                for attr_name in dir(real_basic):
                    if not attr_name.startswith("__"):
                        setattr(self, attr_name, getattr(real_basic, attr_name))
                # Override only the problematic function
                self.is_executable = is_executable

        # Replace the module in sys.modules
        sys.modules["ansible.module_utils.basic"] = BasicModuleType()
    except ImportError:
        # If import fails, raise the error since Ansible should always be available
        raise


# Apply patches that might be needed by Ansible imports
patch_getpass()
setup_pwd_module_mock()
setup_grp_module_mock()
setup_ansible_text_module_mock()
setup_ansible_basic_module_mock()

# Import public functions for easier access
from briefcase_ansible_test.ansible.inventory import parse_ansible_inventory
from briefcase_ansible_test.ansible.ping import ansible_ping_test_with_key, ansible_ping_test
from briefcase_ansible_test.ansible.playbook import parse_ansible_playbook, run_ansible_playbook
