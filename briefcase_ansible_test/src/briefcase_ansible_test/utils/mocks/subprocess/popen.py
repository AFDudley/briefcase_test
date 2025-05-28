"""
Mock Popen implementation for iOS.
"""

import os
import json
import tempfile
import re

from .module_executor import execute_ansible_module
from briefcase_ansible_test.utils.data_processing import (
    parse_command_args,
    extract_ansible_temp_dir,
    build_ansible_module_path,
    format_ansible_result,
    transform_ios_path
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
        # Return realistic output based on command
        stdout = b""
        stderr = b""

        # Parse command using pure function
        cmd_info = parse_command_args(self.args)
        cmd = cmd_info["command"]

        # Use a writable iOS directory instead of /home/mobile
        ios_writable_dir = tempfile.gettempdir()

        if cmd_info["is_echo"]:
            stdout = f"{ios_writable_dir}\n".encode()
        elif cmd_info["is_mkdir"] and ".ansible/tmp" in cmd:
            # Extract the temp directory name from mkdir command
            temp_dir = extract_ansible_temp_dir(cmd)
            if temp_dir:
                ios_ansible_dir = f"{ios_writable_dir}/.ansible/tmp/{temp_dir}"
                stdout = f"{temp_dir}={ios_ansible_dir}\n".encode()

                # Actually create the directory
                try:
                    os.makedirs(ios_ansible_dir, exist_ok=True)
                    print(f"iOS_DEBUG: Created directory: {ios_ansible_dir}")
                except Exception as e:
                    print(
                        f"iOS_DEBUG: Failed to create directory {ios_ansible_dir}: {e}"
                    )
            else:
                stdout = f"ansible-tmp-123456789={ios_writable_dir}/.ansible/tmp/ansible-tmp-123456789\n".encode()
        elif cmd_info["is_test"]:
            # File existence tests - return success (empty output, returncode 0)
            stdout = b""
        elif cmd_info["is_which"]:
            # which command - return a fake path
            stdout = b"/usr/bin/fake\n"
        elif cmd_info["is_chmod"]:
            # chmod commands - just return success
            stdout = b""
        elif cmd_info["is_ansible_module"]:
            # Real Ansible module execution - actually run the module
            print(f"iOS_DEBUG: Attempting to execute real Ansible module: {cmd}")

            try:
                # Extract the path to the AnsiballZ_ping.py file using pure function
                module_path = build_ansible_module_path(cmd)
                if module_path:
                    print(f"iOS_DEBUG: Found module path: {module_path}")

                    try:
                        # Actually execute the Ansible module within our Python interpreter
                        result = execute_ansible_module(module_path)
                        stdout = result.encode() + b"\n"
                        print(
                            f"iOS_DEBUG: Module execution successful, result length: {len(result)}"
                        )
                    except Exception as e:
                        print(f"iOS_DEBUG: Module execution failed: {e}")
                        print(f"iOS_DEBUG: Exception type: {type(e)}")
                        import traceback

                        print(
                            f"iOS_DEBUG: Exception traceback: {traceback.format_exc()}"
                        )
                        # Return an error in Ansible's expected format using pure function
                        error_result = format_ansible_result(
                            success=False,
                            message=f"Module execution failed: {str(e)}",
                            exception=str(e)
                        )
                        stdout = json.dumps(error_result).encode() + b"\n"
                else:
                    print(f"iOS_DEBUG: Could not extract module path from command")
                    error_result = format_ansible_result(
                        success=False,
                        message="Could not parse module path"
                    )
                    stdout = json.dumps(error_result).encode() + b"\n"

            except Exception as top_level_e:
                print(
                    f"iOS_DEBUG: TOP LEVEL EXCEPTION in subprocess mock: {top_level_e}"
                )
                print(f"iOS_DEBUG: Top level exception type: {type(top_level_e)}")
                import traceback

                print(f"iOS_DEBUG: Top level traceback: {traceback.format_exc()}")
                # Return a basic error
                stdout = b'{"failed": true, "msg": "Subprocess mock crashed"}\n'
        else:
            # Default for unknown commands
            stdout = b"success\n"

        return (stdout, stderr)

    def wait(self, timeout=None):
        return 0

    def poll(self):
        return 0

    def terminate(self):
        pass

    def kill(self):
        pass
