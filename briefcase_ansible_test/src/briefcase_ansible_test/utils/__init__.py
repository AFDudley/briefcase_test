"""
Utility modules for briefcase_ansible_test.

This package contains various utility modules for the briefcase_ansible_test application.
"""

# Core utilities
from .system_utils import simple_getuser

# Mock modules for iOS compatibility
from .mocks import (
    PwdModule,
    setup_pwd_module_mock,
    GrpModule,
    setup_grp_module_mock,
    MockPopen,
    setup_subprocess_mock,
)

# iOS-specific patches
from .ios_patches import (
    patch_getpass,
    setup_multiprocessing_mock,
)

__all__ = [
    # Core utilities
    "simple_getuser",
    # Mock modules
    "PwdModule",
    "setup_pwd_module_mock",
    "GrpModule",
    "setup_grp_module_mock",
    "MockPopen",
    "setup_subprocess_mock",
    # iOS patches
    "patch_getpass",
    "setup_multiprocessing_mock",
]
