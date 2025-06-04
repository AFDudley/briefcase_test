#!/usr/bin/env python3
"""
SSH-based tests for venv_management executor.py functions using real remote connections.

Tests the same 4 core scenarios as test_venv_executor.py but with real SSH connections
to night2.lan using the actual inventory file and SSH keys.
"""

import sys
import tempfile
import subprocess
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

# Mock iOS dependencies before importing
sys.modules["rubicon"] = MagicMock()
sys.modules["rubicon.objc"] = MagicMock()


class TestVenvManagementSSH:
    """Test executor.py functions with real SSH connections to night2.lan."""

    @pytest.fixture
    def ssh_check(self):
        """Check SSH connectivity to night2.lan."""
        ssh_key_path = str(
            Path(__file__).parent.parent
            / "src"
            / "briefcase_ansible_test"
            / "resources"
            / "keys"
            / "briefcase_test_key"
        )

        ssh_test = subprocess.run(
            [
                "ssh",
                "-i",
                ssh_key_path,
                "-o",
                "ConnectTimeout=5",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "mtm@night2.lan",
                "echo test",
            ],
            capture_output=True,
        )

        if ssh_test.returncode != 0:
            pytest.skip("SSH to mtm@night2.lan failed")

        return True

    @pytest.fixture
    def temp_dir(self):
        """Create test directory with playbook."""
        with tempfile.TemporaryDirectory() as temp_dir:
            playbook_dir = Path(temp_dir) / "playbooks"
            playbook_dir.mkdir()

            (playbook_dir / "venv_wrapper.yml").write_text(
                """---
- name: Test venv wrapper on remote host
  hosts: "{{ target_host | default('night2.lan') }}"
  remote_user: mtm
  gather_facts: no
  tasks:
    - name: Test task on remote host
      debug:
        msg: "SSH test on {{ inventory_hostname }}"
"""
            )

            yield str(temp_dir)

    @pytest.fixture
    def paths(self):
        """Get paths to inventory and SSH key."""
        base = (
            Path(__file__).parent.parent
            / "src"
            / "briefcase_ansible_test"
            / "resources"
        )
        return {
            "inventory": str(base / "inventory" / "sample_inventory.ini"),
            "ssh_key": str(base / "keys" / "briefcase_test_key"),
        }

    def test_temporary_venv_no_name_ssh(self, ssh_check, temp_dir, paths):
        """Test temporary venv via SSH."""
        result = run_playbook_with_venv(
            venv_wrapper_playbook_path=f"{temp_dir}/playbooks/venv_wrapper.yml",
            inventory_path=paths["inventory"],
            ssh_key_path=paths["ssh_key"],
            metadata_dir_path=temp_dir,
            playbook_path="/path/to/playbook.yml",
            target_host="night2.lan",
            persist=False,
            venv_name=None,
        )

        assert result.success is True
        assert result.result_code == 0
        assert result.venv_name.startswith("temp_")
        assert result.venv_metadata["target_host"] == "night2.lan"

    def test_persistent_venv_with_existing_ssh(self, ssh_check, temp_dir, paths):
        """Test persistent venv with existing metadata via SSH."""
        save_venv_metadata(
            temp_dir,
            "ssh_prod",
            {
                "venv_name": "ssh_prod",
                "target_host": "night2.lan",
                "persistent": True,
                "created_at": "2024-01-01 09:00:00",
            },
        )

        result = run_playbook_with_venv(
            venv_wrapper_playbook_path=f"{temp_dir}/playbooks/venv_wrapper.yml",
            inventory_path=paths["inventory"],
            ssh_key_path=paths["ssh_key"],
            metadata_dir_path=temp_dir,
            playbook_path="/path/to/playbook.yml",
            target_host="night2.lan",
            persist=True,
            venv_name="ssh_prod",
        )

        assert result.success is True
        assert result.result_code == 0
        assert any("Using existing venv" in msg for msg in result.messages)
        assert result.existing_metadata["venv_name"] == "ssh_prod"

    def test_failed_execution_ssh(self, ssh_check, temp_dir, paths):
        """Test failed execution via SSH."""
        broken_playbook = Path(temp_dir) / "broken.yml"
        broken_playbook.write_text(
            """---
- name: Broken playbook
  hosts: night2.lan
  remote_user: mtm
  tasks:
    - name: Fail task
      fail:
        msg: "Test failure"
"""
        )

        result = run_playbook_with_venv(
            venv_wrapper_playbook_path=str(broken_playbook),
            inventory_path=paths["inventory"],
            ssh_key_path=paths["ssh_key"],
            metadata_dir_path=temp_dir,
            playbook_path="/path/to/playbook.yml",
            target_host="night2.lan",
            venv_name="failing",
        )

        assert result.success is False
        assert result.result_code != 0
        assert load_venv_metadata(temp_dir, "failing", "night2.lan") is None

    def test_all_parameters_flow_through_ssh(self, ssh_check, temp_dir, paths):
        """Test all parameters via SSH."""
        result = run_playbook_with_venv(
            venv_wrapper_playbook_path=f"{temp_dir}/playbooks/venv_wrapper.yml",
            inventory_path=paths["inventory"],
            ssh_key_path=paths["ssh_key"],
            metadata_dir_path=temp_dir,
            playbook_path="/custom/ssh/playbook.yml",
            target_host="night2.lan",
            persist=True,
            venv_name="ssh_custom_venv",
            collections=["custom.collection"],
            python_packages=["custom-package", "ansible-core"],
            extra_vars={"custom_var": "ssh_value", "debug": True},
        )

        assert result.success is True
        assert result.result_code == 0

        saved = load_venv_metadata(temp_dir, "ssh_custom_venv", "night2.lan")
        assert saved["venv_name"] == "ssh_custom_venv"
        assert saved["persistent"] is True
        assert saved["target_host"] == "night2.lan"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
