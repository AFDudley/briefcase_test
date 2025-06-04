"""
Ansible utilities for briefcase_ansible_test

This module contains Ansible-related functionality for iOS-compatible operations.
"""

import sys
import types
import os
import stat
import platform
from typing import Any, Union

# Import multiprocessing - use iOS version if available, otherwise standard
try:
    import ios_multiprocessing as multiprocessing  # type: ignore[import-untyped]

    multiprocessing.patch_system_modules()  # type: ignore[attr-defined]

    # iOS-specific setup - only run when ios_multiprocessing is available
    from briefcase_ansible_test.utils import (
        patch_getpass,
        setup_pwd_module_mock,
        setup_grp_module_mock,
        setup_subprocess_mock,
    )

    # Apply iOS-specific patches
    patch_getpass()
    setup_pwd_module_mock()
    setup_grp_module_mock()
    setup_subprocess_mock()

    print("iOS_DEBUG: Applied iOS-specific patches")

except ImportError:
    import multiprocessing

    print("iOS_DEBUG: Using standard multiprocessing (no iOS patches)")

# Import SSH utilities for Paramiko patching - needed on all platforms
from briefcase_ansible_test.ssh_utils import patch_paramiko_for_async


# Apply patch for Paramiko's async keyword issue - needed before Ansible imports
patch_paramiko_for_async()


# Define functions needed for Ansible mocks - only used on iOS
def is_executable(path: str) -> bool:
    """
    Check if a file is executable, with cross-platform compatibility.
    """
    if not os.path.exists(path):
        return False
    file_mode = os.stat(path).st_mode
    return bool(
        (file_mode & stat.S_IXUSR) or path.endswith((".sh", ".py", ".bin", ".exe"))
    )


def setup_ansible_text_module_mock():
    """Install a mock for ansible.module_utils._text in sys.modules."""

    class TextModuleType(types.ModuleType):
        def __init__(self) -> None:
            super().__init__("ansible.module_utils._text")

        def to_native(self, x: Any, errors: str = "strict") -> str:
            return str(x)

        def to_bytes(
            self, obj: Any, encoding: str = "utf-8", errors: str = "strict"
        ) -> Union[bytes, Any]:
            return obj.encode(encoding, errors) if isinstance(obj, str) else obj

        def to_text(
            self, obj: Any, encoding: str = "utf-8", errors: str = "strict"
        ) -> str:
            return obj.decode(encoding, errors) if isinstance(obj, bytes) else str(obj)

    sys.modules["ansible.module_utils._text"] = TextModuleType()


def setup_ansible_basic_module_mock():
    """Patch ansible.module_utils.basic to use our is_executable implementation."""
    try:
        import ansible.module_utils.basic as real_basic

        class BasicModuleType(types.ModuleType):
            def __init__(self):
                super().__init__("ansible.module_utils.basic")
                for attr_name in dir(real_basic):
                    if not attr_name.startswith("__"):
                        setattr(self, attr_name, getattr(real_basic, attr_name))
                self.is_executable = is_executable

        sys.modules["ansible.module_utils.basic"] = BasicModuleType()
    except ImportError:
        raise


print(f"iOS_DEBUG: platform.system() = {platform.system()}")
if platform.system() == "iOS":
    setup_ansible_text_module_mock()
    setup_ansible_basic_module_mock()
    print("iOS_DEBUG: Applied Ansible module mocks")

# Patch ansible.utils.multiprocessing only on iOS
# On standard platforms, let Ansible use its own multiprocessing
if platform.system() == "iOS":
    # First ensure ansible.utils exists
    if "ansible.utils" not in sys.modules:
        import ansible.utils  # type: ignore[import-untyped]

    # Create the multiprocessing submodule
    multiprocessing_utils_module = types.ModuleType("ansible.utils.multiprocessing")
    # Use the iOS multiprocessing
    multiprocessing_utils_module.context = multiprocessing  # type: ignore[attr-defined]
    sys.modules["ansible.utils.multiprocessing"] = multiprocessing_utils_module
    print("iOS_DEBUG: Patched ansible.utils.multiprocessing with iOS version")
else:
    print(
        "iOS_DEBUG: Skipping ansible.utils.multiprocessing patch "
        "(using Ansible's default)"
    )

# Mock ansible.cli.scripts and setup collections only on iOS
if platform.system() == "iOS":
    print("iOS_DEBUG: Creating mock for ansible.cli.scripts")

    # Import ansible first
    import ansible

    # Create parent modules if needed
    if "ansible.cli" not in sys.modules:
        cli_module = types.ModuleType("ansible.cli")
        cli_module.__path__ = ["/mock/ansible/cli"]
        sys.modules["ansible.cli"] = cli_module
        setattr(ansible, "cli", cli_module)

    # Create the scripts module
    cli_scripts_module = types.ModuleType("ansible.cli.scripts")
    cli_scripts_module.__file__ = "/mock/ansible/cli/scripts/__init__.py"
    cli_scripts_module.__path__ = ["/mock/ansible/cli/scripts"]
    sys.modules["ansible.cli.scripts"] = cli_scripts_module
    setattr(sys.modules["ansible.cli"], "scripts", cli_scripts_module)

    print("iOS_DEBUG: Mock ansible.cli.scripts created")

    # Set up ansible_collections module hierarchy for iOS
    from .collections_setup import setup_ansible_collections

    setup_ansible_collections()
else:
    print("iOS_DEBUG: Skipping iOS-specific mocks (using real multiprocessing)")
