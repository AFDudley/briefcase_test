"""
Mock implementations for iOS compatibility.

This module provides mock implementations of system modules that are not
available on iOS, such as pwd, grp, and subprocess.
"""

from .pwd_mock import PwdModule, setup_pwd_module_mock
from .grp_mock import GrpModule, setup_grp_module_mock
from .subprocess_mock import MockPopen, setup_subprocess_mock

__all__ = [
    "PwdModule",
    "setup_pwd_module_mock",
    "GrpModule",
    "setup_grp_module_mock",
    "MockPopen",
    "setup_subprocess_mock",
]
