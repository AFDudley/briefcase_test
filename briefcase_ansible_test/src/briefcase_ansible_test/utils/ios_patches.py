"""
iOS-specific patches and utilities.

This module contains iOS-specific patches that need to be applied to make
standard Python libraries work on iOS.
"""

import getpass

from .system_utils import simple_getuser


def patch_getpass():
    """
    Replace getpass.getuser with our simple_getuser implementation.

    This should be called before any code that might use getpass.getuser.
    """
    getpass.getuser = simple_getuser


def setup_multiprocessing_mock():
    """
    Install our threading-based multiprocessing implementation in sys.modules.

    This replaces the standard multiprocessing module with our iOS-compatible
    threading-based implementation that works without fork() or sem_open().
    """
    # Import our threading-based multiprocessing implementation
    from briefcase_ansible_test.utils.multiprocessing import patch_system_modules

    # Apply the patch to replace multiprocessing with our implementation
    patch_system_modules()
