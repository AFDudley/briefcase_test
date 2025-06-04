#!/usr/bin/env python3
"""
Local tests for venv_management executor.py functions using real Ansible.

Tests the same 4 core scenarios as test_venv_executor.py but with real
execution instead of mocks.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Import the main function we'll test
from briefcase_ansible_test.ansible.venv_management.executor import (
    run_playbook_with_venv,
)
from briefcase_ansible_test.ansible.venv_management.metadata import (
    save_venv_metadata,
    load_venv_metadata,
)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Mock iOS dependencies before importing, but NOT multiprocessing for local tests
sys.modules["rubicon"] = MagicMock()
sys.modules["rubicon.objc"] = MagicMock()
# Don't mock ios_multiprocessing - we want real multiprocessing for local tests


class TestVenvManagementLocal:
    """Test executor.py functions with real Ansible execution - no mocks."""

    @pytest.fixture
    def temp_dir(self):
        """Create test directory structure with required files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)

            # Create required directory structure using variables for efficiency
            playbook_dir = base_dir / "ansible" / "venv_management" / "playbooks"
            inventory_dir = base_dir / "resources" / "inventory"
            keys_dir = base_dir / "resources" / "keys"

            playbook_dir.mkdir(parents=True)
            inventory_dir.mkdir(parents=True)
            keys_dir.mkdir(parents=True)

            # Create minimal test playbook
            (playbook_dir / "venv_wrapper.yml").write_text(
                """---
- name: Test venv wrapper
  hosts: localhost
  connection: local
  gather_facts: no
  tasks:
    - name: Test task
      debug:
        msg: "Test venv management with real execution"
"""
            )

            # Create inventory file
            (inventory_dir / "sample_inventory.ini").write_text(
                "[localhost]\nlocalhost ansible_connection=local"
            )

            # Create SSH key file
            (keys_dir / "briefcase_test_key").touch()

            yield str(base_dir)

    def test_temporary_venv_no_name(self, temp_dir):
        """Test with temporary venv and auto-generated name using real Ansible.

        This tests:
        - generate_temp_venv_name() - called when venv_name is None
        - get_venv_path() - called with persist=False
        - create_venv_vars() - with minimal params
        - create_ansible_context() - for localhost
        - create_default_metadata() - for temp venv
        """
        # Check if ansible-playbook is available
        import subprocess

        ansible_check = subprocess.run(
            ["which", "ansible-playbook"], capture_output=True, text=True
        )
        if ansible_check.returncode != 0:
            pytest.skip("ansible-playbook not installed on system")

        # Build paths using variables for efficiency
        playbook_path = f"{temp_dir}/ansible/venv_management/playbooks/venv_wrapper.yml"
        inventory_path = f"{temp_dir}/resources/inventory/sample_inventory.ini"
        ssh_key_path = f"{temp_dir}/resources/keys/briefcase_test_key"

        result = run_playbook_with_venv(
            venv_wrapper_playbook_path=playbook_path,
            inventory_path=inventory_path,
            ssh_key_path=ssh_key_path,
            metadata_dir_path=temp_dir,
            playbook_path="/path/to/playbook.yml",
            target_host="localhost",
            persist=False,
            venv_name=None,  # Forces generate_temp_venv_name()
        )

        # Should succeed with real Ansible
        assert result.success is True
        assert result.result_code == 0

        # Verify temp venv name was generated and used
        assert result.venv_name.startswith(
            "temp_"
        ), f"Expected temp_ venv name, got {result.venv_name}"

        # Verify metadata was saved
        assert result.venv_metadata is not None
        assert result.venv_metadata["venv_name"] == result.venv_name

        print("\nTemporary venv test completed successfully!")

    def test_persistent_venv_with_existing(self, temp_dir):
        """Test with persistent venv that already exists using real Ansible.

        This tests:
        - load_venv_metadata() - checking for existing venv
        - get_venv_path() - called with persist=True
        - create_venv_vars() - with all params
        - Message formatting for existing venv
        """
        # Check if ansible-playbook is available
        import subprocess

        ansible_check = subprocess.run(
            ["which", "ansible-playbook"], capture_output=True, text=True
        )
        if ansible_check.returncode != 0:
            pytest.skip("ansible-playbook not installed on system")

        # Create existing metadata
        existing_metadata = {
            "venv_name": "prod_venv",
            "venv_path": "~/ansible-venvs/prod_venv",
            "target_host": "localhost",  # Use localhost for real execution
            "persistent": True,
            "created_at": "2024-01-01 09:00:00",
        }
        save_venv_metadata(temp_dir, "prod_venv", existing_metadata)

        # Build paths using variables for efficiency
        playbook_path = f"{temp_dir}/ansible/venv_management/playbooks/venv_wrapper.yml"
        inventory_path = f"{temp_dir}/resources/inventory/sample_inventory.ini"
        ssh_key_path = f"{temp_dir}/resources/keys/briefcase_test_key"

        result = run_playbook_with_venv(
            venv_wrapper_playbook_path=playbook_path,
            inventory_path=inventory_path,
            ssh_key_path=ssh_key_path,
            metadata_dir_path=temp_dir,
            playbook_path="/path/to/playbook.yml",
            target_host="localhost",  # Use localhost for real execution
            persist=True,
            venv_name="prod_venv",
            collections=["community.general", "ansible.posix"],
            python_packages=["ansible-core", "paramiko"],
            extra_vars={"api_key": "secret"},
        )

        # Should succeed with real Ansible
        assert result.success is True
        assert result.result_code == 0

        # Verify existing venv message was included
        assert any(
            "Using existing venv" in msg for msg in result.messages
        ), f"Expected existing venv message in {result.messages}"

        # Verify existing metadata is available
        assert result.existing_metadata is not None
        assert result.existing_metadata["venv_name"] == "prod_venv"

        print("\nPersistent venv with existing metadata test completed successfully!")

    def test_failed_execution(self, temp_dir):
        """Test handling of failed execution using real Ansible.

        This tests:
        - Metadata is NOT saved on failure
        - Return value is False
        """
        # Create a broken playbook to force failure
        broken_playbook_path = Path(temp_dir) / "broken_venv_wrapper.yml"
        broken_playbook_path.write_text(
            """---
- name: Broken playbook
  hosts: localhost
  connection: local
  gather_facts: no
  tasks:
    - name: This task will fail
      fail:
        msg: "Intentional failure for testing"
"""
        )

        # Check if ansible-playbook is available
        import subprocess

        ansible_check = subprocess.run(
            ["which", "ansible-playbook"], capture_output=True, text=True
        )
        if ansible_check.returncode != 0:
            pytest.skip("ansible-playbook not installed on system")

        # Build paths using variables for efficiency
        inventory_path = f"{temp_dir}/resources/inventory/sample_inventory.ini"
        ssh_key_path = f"{temp_dir}/resources/keys/briefcase_test_key"

        result = run_playbook_with_venv(
            venv_wrapper_playbook_path=str(broken_playbook_path),
            inventory_path=inventory_path,
            ssh_key_path=ssh_key_path,
            metadata_dir_path=temp_dir,
            playbook_path="/path/to/playbook.yml",
            target_host="localhost",
            venv_name="failing_venv",
        )

        # Should fail due to broken playbook
        assert result.success is False
        assert result.result_code != 0

        # Verify metadata was NOT saved
        loaded = load_venv_metadata(temp_dir, "failing_venv", "localhost")
        assert loaded is None

        # Verify no success messages about metadata
        assert not any(
            "Metadata saved" in msg for msg in result.messages
        ), f"Unexpected metadata save message in {result.messages}"

        print("\nFailed execution test completed successfully!")

    def test_all_parameters_flow_through(self, temp_dir):
        """Test that all parameters flow through the function chain correctly
        using real Ansible.

        This verifies the integration of:
        - create_venv_vars() receiving all inputs
        - create_ansible_context() with localhost (avoiding SSH complexity)
        - create_default_metadata() with all fields
        """
        # Check if ansible-playbook is available
        import subprocess

        ansible_check = subprocess.run(
            ["which", "ansible-playbook"], capture_output=True, text=True
        )
        if ansible_check.returncode != 0:
            pytest.skip("ansible-playbook not installed on system")

        # Build paths using variables for efficiency
        playbook_path = f"{temp_dir}/ansible/venv_management/playbooks/venv_wrapper.yml"
        inventory_path = f"{temp_dir}/resources/inventory/sample_inventory.ini"
        ssh_key_path = f"{temp_dir}/resources/keys/briefcase_test_key"

        result = run_playbook_with_venv(
            venv_wrapper_playbook_path=playbook_path,
            inventory_path=inventory_path,
            ssh_key_path=ssh_key_path,
            metadata_dir_path=temp_dir,
            playbook_path="/custom/playbook.yml",
            target_host="localhost",  # Use localhost to avoid SSH complexity in tests
            persist=True,
            venv_name="custom_venv",
            collections=["custom.collection"],
            python_packages=["custom-package", "ansible-core"],
            extra_vars={"custom_var": "custom_value", "debug": True},
        )

        # Should succeed with real Ansible
        assert result.success is True
        assert result.result_code == 0

        # Verify metadata was saved with correct values
        saved = load_venv_metadata(temp_dir, "custom_venv", "localhost")
        assert saved is not None
        assert saved["venv_name"] == "custom_venv"
        assert saved["persistent"] is True
        assert saved["target_host"] == "localhost"

        # Verify success message was included
        assert any(
            "Metadata saved" in msg for msg in result.messages
        ), f"Expected success message in {result.messages}"

        # Verify result structure
        assert result.venv_name == "custom_venv"
        assert result.venv_metadata is not None
        assert result.existing_metadata is None  # Should be None for new venv

        print("\nAll parameters flow through test completed successfully!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
