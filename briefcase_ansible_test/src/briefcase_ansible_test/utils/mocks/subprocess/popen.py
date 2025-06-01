"""
Mock Popen implementation for iOS.
"""

import os
import json
import tempfile

from .module_executor import execute_ansible_module
from briefcase_ansible_test.utils.data_processing import (
    parse_command_args,
    extract_ansible_temp_dir,
    build_ansible_module_path,
    format_ansible_result,
)


class MockPopen:
    """Mock implementation of subprocess.Popen for iOS."""

    def __init__(self, args, **kwargs):
        print(f"iOS_DEBUG: Mocked subprocess.Popen call: {args}")
        self.args = args
        self.returncode = 0
        self.stdout = kwargs.get("stdout")
        self.stderr = kwargs.get("stderr")
        self.stdin = kwargs.get("stdin")
        self.pid = 12345  # Fake PID

    def communicate(self, input=None, timeout=None):
        """Return realistic output based on command."""
        cmd_info = parse_command_args(self.args)
        cmd = cmd_info["command"]
        ios_dir = tempfile.gettempdir()

        # Simple dispatch with inline handlers
        if cmd_info["is_echo"]:
            return f"{ios_dir}\n".encode(), b""

        elif cmd_info["is_mkdir"] and ".ansible/tmp" in cmd:
            temp_dir = extract_ansible_temp_dir(cmd)
            if not temp_dir:
                raise ValueError("Could not extract temp directory from mkdir command")
            ios_ansible_dir = f"{ios_dir}/.ansible/tmp/{temp_dir}"
            os.makedirs(ios_ansible_dir, exist_ok=True)
            print(f"iOS_DEBUG: Created directory: {ios_ansible_dir}")
            return f"{temp_dir}={ios_ansible_dir}\n".encode(), b""

        elif cmd_info["is_test"] or cmd_info["is_chmod"]:
            return b"", b""  # Success

        elif cmd_info["is_which"]:
            return b"/usr/bin/fake\n", b""

        elif cmd_info["is_ansible_module"]:
            # Execute ansible module
            print(f"iOS_DEBUG: Executing Ansible module: {cmd}")
            module_path = build_ansible_module_path(cmd)
            
            if not module_path:
                raise ValueError("Could not parse module path from ansible command")
            
            result = execute_ansible_module(module_path)
            print(f"iOS_DEBUG: Module success, len: {len(result)}")
            return result.encode() + b"\n", b""

        else:
            return b"success\n", b""  # Default

    def wait(self, timeout=None):
        return 0

    def poll(self):
        return 0

    def terminate(self):
        pass

    def kill(self):
        pass
