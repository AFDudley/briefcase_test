"""
Ansible utilities for briefcase_ansible_test

This module contains Ansible-related functionality for iOS-compatible operations.
"""

# Ensure system mocks are set up before importing anything else
from briefcase_ansible_test.utils.system_utils import (
    patch_getpass,
    setup_pwd_module_mock,
    setup_grp_module_mock,
    setup_ansible_text_module_mock,
    setup_ansible_basic_module_mock
)

# Apply patches that might be needed by Ansible imports
patch_getpass()
setup_pwd_module_mock()
setup_grp_module_mock()
setup_ansible_text_module_mock()
setup_ansible_basic_module_mock()

# Import public functions for easier access
from briefcase_ansible_test.ansible.inventory import parse_ansible_inventory
from briefcase_ansible_test.ansible.ping import ansible_ping_test_with_key