"""
Pytest configuration for _multiprocessing tests.
"""

import sys
import os
from pathlib import Path

# Add src to Python path for tests
src_path = Path(__file__).parent.parent.parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# Apply iOS compatibility patches for all tests
from briefcase_ansible_test.utils.system_utils import (
    setup_pwd_module_mock,
    setup_grp_module_mock,
    patch_getpass,
)


def pytest_configure(config):
    """Configure pytest for multiprocessing tests."""
    # Apply system compatibility patches
    setup_pwd_module_mock()
    setup_grp_module_mock()
    patch_getpass()

    # Apply multiprocessing patches
    from briefcase_ansible_test.utils._multiprocessing import _patch_system_modules

    _patch_system_modules()


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Mark tests based on their location
        if "integration" in str(item.fspath):
            item.add_marker("integration")
        elif "system" in str(item.fspath):
            item.add_marker("system")
        else:
            item.add_marker("unit")
