#!/usr/bin/env python3
"""
SSH-based tests for venv_management executor.py functions using real remote connections.

Tests the same 4 core scenarios as test_venv_executor.py but with real SSH connections
to night2.lan using the actual inventory file and SSH keys.
"""
# flake8: noqa: E402

import subprocess
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from briefcase_ansible_test.ansible.venv_management.executor import (
    run_playbook_with_venv,
)
from briefcase_ansible_test.ansible.venv_management.metadata import (
    load_venv_metadata,
    save_venv_metadata,
)


class TestVenvManagementSSH:
    """Test executor.py functions with real SSH connections to night2.lan."""

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

    @pytest.fixture
    def ssh_check(self, paths):
        """Check SSH connectivity to night2.lan using ansible ping."""
        result = subprocess.run(
            [
                "ansible",
                "night2.lan",
                "-i",
                paths["inventory"],
                "--private-key",
                paths["ssh_key"],
                "-u",
                "mtm",
                "-m",
                "ping",
            ],
            capture_output=True,
        )

        if result.returncode != 0:
            pytest.skip("Ansible ping to night2.lan failed")

        return True

    @pytest.fixture
    def temp_dir(self):
        """Create test directory with SSH playbook."""
        with tempfile.TemporaryDirectory() as temp_dir:
            playbook_dir = Path(temp_dir) / "playbooks"
            playbook_dir.mkdir()

            # Load test SSH playbook from disk
            test_ssh_playbook_path = Path(__file__).parent / "test_ssh_playbook.yml"

            # Create wrapper that uses include_tasks to load from the test file
            wrapper_content = f"""---
- name: Test venv wrapper on remote host via SSH
  hosts: "{{{{ target_host | default('night2.lan') }}}}"
  remote_user: mtm
  connection: ssh
  gather_facts: no
  vars:
    ansible_ssh_private_key_file: "{{{{ ssh_key_path }}}}"
    ansible_ssh_common_args: '-o StrictHostKeyChecking=no -o ControlMaster=no'
  tasks:
    - name: Include SSH test tasks from file
      include_tasks: {test_ssh_playbook_path}
"""
            (playbook_dir / "venv_wrapper.yml").write_text(wrapper_content)

            yield str(temp_dir)

    def test_temporary_venv_no_name_ssh(self, ssh_check, temp_dir, paths):
        """Test temporary venv via SSH - confirms real remote execution."""
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
  connection: ssh
  vars:
    ansible_ssh_private_key_file: "{{ ssh_key_path }}"
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
