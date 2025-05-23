"""
Subprocess mock implementation for iOS.

This package provides a complete mock of the subprocess module for iOS,
where creating actual subprocesses is not supported.
"""

from .completed_process import MockCompletedProcess
from .popen import MockPopen
from .mock_functions import setup_subprocess_mock

__all__ = [
    "MockCompletedProcess",
    "MockPopen",
    "setup_subprocess_mock",
]