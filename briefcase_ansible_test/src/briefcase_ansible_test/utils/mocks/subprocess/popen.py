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


def _handle_echo_command(cmd, cmd_info):
    """Handle echo commands."""
    ios_writable_dir = tempfile.gettempdir()
    return f"{ios_writable_dir}\n".encode(), b""


def _handle_mkdir_command(cmd, cmd_info):
    """Handle mkdir commands, especially for Ansible temp directories."""
    ios_writable_dir = tempfile.gettempdir()

    if ".ansible/tmp" in cmd:
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
                print(f"iOS_DEBUG: Failed to create directory {ios_ansible_dir}: {e}")

            return stdout, b""
        else:
            tmp_dir = "ansible-tmp-123456789"
            tmp_path = f"{ios_writable_dir}/.ansible/tmp/{tmp_dir}"
            return f"{tmp_dir}={tmp_path}\n".encode(), b""

    # For other mkdir commands, just return success
    return b"", b""


def _handle_test_command(cmd, cmd_info):
    """Handle test commands (file existence tests)."""
    # Return success (empty output, returncode 0)
    return b"", b""


def _handle_ansible_module(cmd, cmd_info):
    """Handle Ansible module execution."""
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
                result_len = len(result)
                msg = f"iOS_DEBUG: Module execution successful, len: {result_len}"
                print(msg)
                return stdout, b""
            except Exception as e:
                print(f"iOS_DEBUG: Module execution failed: {e}")
                print(f"iOS_DEBUG: Exception type: {type(e)}")
                import traceback

                print(f"iOS_DEBUG: Exception traceback: {traceback.format_exc()}")

                # Return an error in Ansible's expected format using pure function
                error_result = format_ansible_result(
                    success=False,
                    message=f"Module execution failed: {str(e)}",
                    exception=str(e),
                )
                return json.dumps(error_result).encode() + b"\n", b""
        else:
            print("iOS_DEBUG: Could not extract module path from command")
            error_result = format_ansible_result(
                success=False, message="Could not parse module path"
            )
            return json.dumps(error_result).encode() + b"\n", b""

    except Exception as top_level_e:
        print(f"iOS_DEBUG: TOP LEVEL EXCEPTION in subprocess mock: {top_level_e}")
        print(f"iOS_DEBUG: Top level exception type: {type(top_level_e)}")
        import traceback

        print(f"iOS_DEBUG: Top level traceback: {traceback.format_exc()}")
        # Return a basic error
        return b'{"failed": true, "msg": "Subprocess mock crashed"}\n', b""


def _handle_which_command(cmd, cmd_info):
    """Handle which commands."""
    return b"/usr/bin/fake\n", b""


def _handle_chmod_command(cmd, cmd_info):
    """Handle chmod commands."""
    # Just return success
    return b"", b""


def _handle_default_command(cmd, cmd_info):
    """Handle unknown commands."""
    return b"success\n", b""


# Command handler dispatch dictionary
COMMAND_HANDLERS = {
    "echo": _handle_echo_command,
    "mkdir": _handle_mkdir_command,
    "test": _handle_test_command,
    "ansible_module": _handle_ansible_module,
    "which": _handle_which_command,
    "chmod": _handle_chmod_command,
    "default": _handle_default_command,
}


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
        """
        Simulate process communication using dispatch pattern.

        Args:
            input: Input data to send to process
            timeout: Timeout for communication

        Returns:
            tuple: (stdout, stderr) as bytes
        """
        # Parse command using pure function
        cmd_info = parse_command_args(self.args)
        cmd = cmd_info["command"]

        # Determine which handler to use based on command type
        handler_key = "default"
        if cmd_info["is_echo"]:
            handler_key = "echo"
        elif cmd_info["is_mkdir"]:
            handler_key = "mkdir"
        elif cmd_info["is_test"]:
            handler_key = "test"
        elif cmd_info["is_ansible_module"]:
            handler_key = "ansible_module"
        elif cmd_info["is_which"]:
            handler_key = "which"
        elif cmd_info["is_chmod"]:
            handler_key = "chmod"

        # Get the appropriate handler from dispatch dictionary
        handler = COMMAND_HANDLERS.get(handler_key, COMMAND_HANDLERS["default"])

        # Execute the handler
        stdout, stderr = handler(cmd, cmd_info)

        return (stdout, stderr)

    def wait(self, timeout=None):
        return 0

    def poll(self):
        return 0

    def terminate(self):
        pass

    def kill(self):
        pass
