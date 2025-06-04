"""
Pure functions for data processing and transformation.

This module contains side-effect-free functions for data manipulation,
following functional programming principles.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ButtonConfig:
    """Immutable button configuration."""

    label: str
    callback_name: str
    tooltip: str


@dataclass(frozen=True)
class SSHConfig:
    """Immutable SSH connection configuration."""

    hostname: str
    username: str
    port: int = 22
    key_path: Optional[str] = None


@dataclass(frozen=True)
class AnsibleConfig:
    """Immutable Ansible configuration."""

    inventory_path: str
    key_path: str
    target_host: str
    connection_type: str = "local"
    forks: int = 1


def create_button_configs() -> List[ButtonConfig]:
    """Create button configurations for the application."""
    return [
        ButtonConfig(
            label="Local Ansible Ping Test",
            callback_name="ansible_ping_test",
            tooltip="Run Ansible ping test",
        ),
        ButtonConfig(
            label="Generate ED25519 Key",
            callback_name="generate_ed25519_key",
            tooltip="Generate ED25519 SSH key using cryptography library",
        ),
        ButtonConfig(
            label="Run Playbook in Temp Venv",
            callback_name="test_temp_venv_playbook",
            tooltip="Execute hello_world.yml in temporary virtual environment",
        ),
        ButtonConfig(
            label="Create Named Venv",
            callback_name="test_create_venv",
            tooltip="Create persistent virtual environment with timestamp name",
        ),
        ButtonConfig(
            label="List Venvs",
            callback_name="test_list_venvs",
            tooltip="Show all virtual environments",
        ),
        ButtonConfig(
            label="Delete Venv",
            callback_name="test_delete_venv",
            tooltip="Delete oldest test virtual environment",
        ),
    ]


def parse_command_args(args: List[str]) -> Dict[str, Any]:
    """Parse command arguments into structured data."""
    if not args:
        return {"command": "", "args": []}

    # Convert to string command
    cmd = (
        " ".join(str(arg) for arg in args)
        if isinstance(args, (list, tuple))
        else str(args)
    )

    return {
        "command": cmd,
        "args": args if isinstance(args, (list, tuple)) else [args],
        "is_ansible_module": "AnsiballZ_ping.py" in cmd,
        "is_mkdir": "mkdir -p" in cmd,
        "is_echo": cmd.startswith(("echo ~", "echo $HOME", 'echo "$(pwd)"')),
        "is_test": any(cmd.startswith(f"test {flag}") for flag in ["-e", "-f", "-d"]),
        "is_which": "which " in cmd,
        "is_chmod": "chmod " in cmd,
    }


def extract_ansible_temp_dir(command: str) -> Optional[str]:
    """Extract ansible temp directory name from mkdir command."""
    if "ansible-tmp-" not in command:
        return None

    # Find the temp directory pattern
    parts = command.split()
    for part in parts:
        if "ansible-tmp-" in part:
            # Extract just the directory name
            if "/" in part:
                return part.split("/")[-1]
            return part

    return None


def build_ansible_module_path(command: str) -> Optional[str]:
    """Extract Ansible module path from command."""
    import re

    match = re.search(r"(/[^\s]+/AnsiballZ_ping\.py)", command)
    return match.group(1) if match else None


def format_ansible_result(success: bool, message: str, **kwargs) -> Dict[str, Any]:
    """Format result in Ansible's expected JSON format."""
    result = {
        "changed": False,
        "ping": "pong" if success else "failed",
    }

    if not success:
        result["failed"] = True
        result["msg"] = message

    # Add any additional fields
    result.update(kwargs)

    return result


def transform_inventory_data(
    inventory_hosts: List[str], group_name: str
) -> Dict[str, Any]:
    """Transform inventory host list into structured format."""
    return {
        "groups": {group_name: inventory_hosts},
        "total_hosts": len(inventory_hosts),
        "group_count": 1 if inventory_hosts else 0,
    }


def build_ssh_key_paths(app_path: str, key_type: str = "ed25519") -> Dict[str, str]:
    """Build SSH key file paths."""
    ssh_dir = os.path.join(app_path, "resources", "ssh")
    key_name = f"id_{key_type}"

    return {
        "ssh_dir": ssh_dir,
        "private_key": os.path.join(ssh_dir, key_name),
        "public_key": os.path.join(ssh_dir, f"{key_name}.pub"),
    }


def parse_public_key_string(public_key_content: str) -> Dict[str, Any]:
    """Parse SSH public key string into components."""
    parts = public_key_content.strip().split(None, 2)

    if len(parts) < 2:
        return {"algorithm": "", "key": "", "comment": "", "is_valid": False}

    return {
        "algorithm": parts[0],
        "key": parts[1],
        "comment": parts[2] if len(parts) > 2 else "",
        "is_valid": True,
    }


def categorize_log_level(text: str) -> str:
    """Determine appropriate log level based on text content."""
    text_clean = text.strip()

    # Error indicators
    if any(
        indicator in text_clean for indicator in ["✗", "Error:", "failed:", "Exception"]
    ):
        return "ERROR"

    # Warning indicators
    if any(indicator in text_clean.lower() for indicator in ["⚠", "warning"]):
        return "WARNING"

    # Traceback
    if "traceback" in text_clean.lower():
        return "ERROR"

    # Success indicators
    if text_clean.startswith("✓"):
        return "INFO"

    return "INFO"


def build_ansible_play_dict(
    hosts: str, task_module: str = "ping", task_args: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Build Ansible play dictionary."""
    return {
        "name": f"Test {task_module} on {hosts}",
        "hosts": hosts,
        "gather_facts": False,
        "tasks": [{"name": f"Execute {task_module}", task_module: task_args or {}}],
    }


def transform_ios_path(
    path: str, ios_base: str = "/var/mobile/Containers/Data/Application"
) -> str:
    """Transform a path to iOS-compatible location."""
    # If it's trying to use home directory
    if path.startswith(("~", "$HOME", "/home")):
        # Use iOS app container path
        return ios_base

    # If it's an absolute path that won't work on iOS
    if path.startswith("/") and not path.startswith(("/var", "/tmp", "/private")):
        # Redirect to temp directory
        import tempfile

        return tempfile.gettempdir()

    return path


def extract_test_results(output: str) -> Dict[str, Any]:
    """Extract test results from output text."""
    lines = output.strip().split("\n")

    results = {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "errors": [],
        "warnings": [],
        "success_rate": 0.0,
    }

    for line in lines:
        if "✓" in line:
            results["passed"] += 1
        elif "✗" in line or "failed" in line.lower():
            results["failed"] += 1
            results["errors"].append(line.strip())
        elif "⚠" in line:
            results["warnings"].append(line.strip())

    results["total_tests"] = results["passed"] + results["failed"]
    if results["total_tests"] > 0:
        results["success_rate"] = results["passed"] / results["total_tests"]

    return results
