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
    Install multiprocessing implementation in sys.modules.

    Uses the external ios-multiprocessing package instead of bundled version.
    """
    # Import external ios-multiprocessing package  
    import ios_multiprocessing
    ios_multiprocessing.patch_system_modules()
