"""
Ansible utilities for briefcase_ansible_test

This module contains Ansible-related functionality for iOS-compatible operations.
"""
import sys
import types

# Ensure system mocks are set up before importing anything else
from briefcase_ansible_test.utils.system_utils import (
    patch_getpass,
    setup_pwd_module_mock,
    setup_grp_module_mock,
    setup_ansible_basic_module_mock
)

# Define our own text module mock here instead of importing from system_utils
def setup_ansible_text_module_mock():
    """
    Install a mock for ansible.module_utils._text in sys.modules.
    
    This provides text conversion utilities that Ansible needs.
    """
    class TextModuleType(types.ModuleType):
        def __init__(self):
            super().__init__('ansible.module_utils._text')
            self.to_native = lambda x, errors='strict': str(x)
            self.to_bytes = lambda obj, encoding='utf-8', errors='strict': obj.encode(encoding, errors) if isinstance(obj, str) else obj
            self.to_text = lambda obj, encoding='utf-8', errors='strict': obj.decode(encoding, errors) if isinstance(obj, bytes) else str(obj)
            
    sys.modules['ansible.module_utils._text'] = TextModuleType()

# Apply patches that might be needed by Ansible imports
patch_getpass()
setup_pwd_module_mock()
setup_grp_module_mock()
setup_ansible_text_module_mock()  # Now using our local implementation
setup_ansible_basic_module_mock()

# Import public functions for easier access
from briefcase_ansible_test.ansible.inventory import parse_ansible_inventory
from briefcase_ansible_test.ansible.ping import ansible_ping_test_with_key