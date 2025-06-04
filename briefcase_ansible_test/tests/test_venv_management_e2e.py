#!/usr/bin/env python3
"""
End-to-end test for venv_management using real Ansible components.

This test verifies the complete flow of creating a virtual environment
and executing a real playbook within it.
"""
# flake8: noqa: E402

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from briefcase_ansible_test.ansible.venv_management.executor import (
    run_playbook_with_venv,
)


class TestVenvManagementE2E:
    """End-to-end test for venv management with real playbook execution."""

    def test_real_playbook_execution_in_venv(self):
        """Test executing a real playbook inside the venv using real Ansible.

        This test verifies that the venv_wrapper actually executes a real
        user playbook (hello_world.yml) inside the virtual environment.
        """
        # Check if ansible-playbook is available
        import subprocess

        ansible_check = subprocess.run(
            ["which", "ansible-playbook"], capture_output=True, text=True
        )
        if ansible_check.returncode != 0:
            pytest.skip("ansible-playbook not installed on system")

        # Use real project resources
        project_root = Path(__file__).parent.parent
        src_dir = project_root / "src" / "briefcase_ansible_test"

        # Real paths to actual project files
        real_venv_wrapper_path = str(
            src_dir / "ansible" / "venv_management" / "playbooks" / "venv_wrapper.yml"
        )

        # Use the real inventory and keys from the project
        inventory_path = str(
            src_dir / "resources" / "inventory" / "sample_inventory.ini"
        )
        ssh_key_path = str(src_dir / "resources" / "keys" / "briefcase_test_key")

        # Path to the real hello_world playbook
        hello_world_path = str(src_dir / "resources" / "playbooks" / "hello_world.yml")

        # Use a real directory for metadata
        with tempfile.TemporaryDirectory() as metadata_dir:
            result = run_playbook_with_venv(
                venv_wrapper_playbook_path=real_venv_wrapper_path,
                inventory_path=inventory_path,
                ssh_key_path=ssh_key_path,
                metadata_dir_path=metadata_dir,  # Only temp dir is for metadata storage
                playbook_path=hello_world_path,  # Real playbook to execute in venv
                target_host="localhost",
                persist=False,
                venv_name="hello_world_test",
            )

            # Should succeed with real Ansible
            assert result.success is True
            assert result.result_code == 0

            # Verify metadata was saved
            assert result.venv_metadata is not None
            assert result.venv_name == "hello_world_test"

            print("\nReal playbook execution in venv test completed successfully!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
