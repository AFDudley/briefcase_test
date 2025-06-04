"""
Mock functions for subprocess module.
"""

import subprocess

from .popen import MockPopen
from .completed_process import MockCompletedProcess


def setup_subprocess_mock():
    """
    Mock subprocess module to prevent iOS process creation errors.

    iOS doesn't support creating subprocesses, so we need to mock
    subprocess operations to avoid [Errno 45] Operation not supported.
    """

    def mock_run(args, **kwargs):
        print(f"iOS_DEBUG: Mocked subprocess.run call: {args}")
        # Create a mock process and get realistic output
        mock_proc = MockPopen(args, **kwargs)
        stdout, stderr = mock_proc.communicate()
        return MockCompletedProcess(args, stdout=stdout, stderr=stderr)

    def mock_call(args, **kwargs):
        print(f"iOS_DEBUG: Mocked subprocess.call call: {args}")
        return 0

    def mock_check_call(args, **kwargs):
        print(f"iOS_DEBUG: Mocked subprocess.check_call call: {args}")
        return 0

    def mock_check_output(args, **kwargs):
        print(f"iOS_DEBUG: Mocked subprocess.check_output call: {args}")
        # Return realistic output like Popen does
        mock_proc = MockPopen(args, **kwargs)
        stdout, stderr = mock_proc.communicate()
        return stdout

    # Replace subprocess functions
    subprocess.Popen = MockPopen
    subprocess.run = mock_run
    subprocess.call = mock_call
    subprocess.check_call = mock_check_call
    subprocess.check_output = mock_check_output

    print("iOS_DEBUG: subprocess module mocked for iOS compatibility")
