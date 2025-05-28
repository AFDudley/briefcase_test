"""
Mock Popen implementation for iOS.
"""

import os
import json
import tempfile
import re

from .module_executor import execute_ansible_module


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

        if isinstance(self.args, (list, tuple)) and len(self.args) > 0:
            cmd = " ".join(str(arg) for arg in self.args)
        else:
            cmd = str(self.args)

        # Handle common shell commands that Ansible uses
        # Use a writable iOS directory instead of /home/mobile
        ios_writable_dir = tempfile.gettempdir()

        if "echo ~" in cmd or "echo $HOME" in cmd:
            stdout = f"{ios_writable_dir}\n".encode()
        elif 'echo "$(pwd)"' in cmd or "pwd" in cmd:
            stdout = f"{ios_writable_dir}\n".encode()
        elif "mkdir -p" in cmd and ".ansible/tmp" in cmd:
            # Extract the temp directory name from mkdir command and redirect to writable location
            if "ansible-tmp-" in cmd:
                match = re.search(r"ansible-tmp-[\d\.-]+", cmd)
                if match:
                    temp_dir = match.group(0)
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
            else:
                stdout = f"ansible-tmp-123456789={ios_writable_dir}/.ansible/tmp/ansible-tmp-123456789\n".encode()
        elif "test -e" in cmd or "test -f" in cmd or "test -d" in cmd:
            # File existence tests - return success (empty output, returncode 0)
            stdout = b""
        elif "which " in cmd:
            # which command - return a fake path
            stdout = b"/usr/bin/fake\n"
        elif "chmod " in cmd:
            # chmod commands - just return success
            stdout = b""
        elif "python3" in cmd and "AnsiballZ_ping.py" in cmd:
            # Real Ansible module execution - actually run the module
            print(f"iOS_DEBUG: Attempting to execute real Ansible module: {cmd}")

            try:
                # Extract the path to the AnsiballZ_ping.py file
                match = re.search(r"(/[^\s]+/AnsiballZ_ping\.py)", cmd)
                if match:
                    module_path = match.group(1)
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
                        # Return an error in Ansible's expected format
                        error_result = {
                            "failed": True,
                            "msg": f"Module execution failed: {str(e)}",
                            "exception": str(e),
                        }
                        stdout = json.dumps(error_result).encode() + b"\n"
                else:
                    print(f"iOS_DEBUG: Could not extract module path from command")
                    stdout = b'{"failed": true, "msg": "Could not parse module path"}\n'

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
