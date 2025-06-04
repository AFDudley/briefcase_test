#!/usr/bin/env python3
"""
End-to-End remote tests for venv_management using real SSH connections.

Tests the complete workflow using existing playbooks and resources on disk.
No mocks, no temporary files - uses actual project files.

KISS principle: Simple tests using real files and real remote execution.
"""
# flake8: noqa: E402

import subprocess
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from briefcase_ansible_test.ansible.venv_management.executor import (
    run_playbook_with_venv,
)
from briefcase_ansible_test.ansible.venv_management.metadata import (
    delete_venv_metadata,
    load_venv_metadata,
    save_venv_metadata,
)


class TestVenvManagementE2ERemote:
    """End-to-end tests with real remote venv creation using existing files."""

    @pytest.fixture(scope="class")
    def paths(self):
        """Get paths to existing project files."""
        base = Path(__file__).parent.parent / "src" / "briefcase_ansible_test"
        return {
            "inventory": str(base / "resources" / "inventory" / "sample_inventory.ini"),
            "ssh_key": str(base / "resources" / "keys" / "briefcase_test_key"),
            "venv_wrapper": str(
                base / "ansible" / "venv_management" / "playbooks" / "venv_wrapper.yml"
            ),
            "hello_world": str(base / "resources" / "playbooks" / "hello_world.yml"),
            "metadata_dir": str(Path(__file__).parent.parent),
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
            pytest.skip("Ansible ping to night2.lan failed - SSH not available")

        return True

    def test_e2e_create_new_persistent_venv(self, ssh_check, paths):
        """E2E test: Create new persistent venv using existing venv_wrapper.yml."""
        venv_name = "e2e_test_venv"

        # Clean up any existing metadata first
        delete_venv_metadata(paths["metadata_dir"], venv_name, "night2.lan")

        result = run_playbook_with_venv(
            venv_wrapper_playbook_path=paths["venv_wrapper"],
            inventory_path=paths["inventory"],
            ssh_key_path=paths["ssh_key"],
            metadata_dir_path=paths["metadata_dir"],
            playbook_path=paths["hello_world"],
            target_host="night2.lan",
            persist=True,
            venv_name=venv_name,
            python_packages=["ansible-core"],
            extra_vars={"ansible_user": "mtm"},
        )

        # Verify E2E success
        assert result.success is True, f"E2E test failed: {result.messages}"
        assert result.result_code == 0
        assert result.venv_name == venv_name

        # Verify metadata was saved
        saved_metadata = load_venv_metadata(
            paths["metadata_dir"], venv_name, "night2.lan"
        )
        assert saved_metadata is not None
        assert saved_metadata["venv_name"] == venv_name
        assert saved_metadata["persistent"] is True

        # Verify that the operations completed successfully
        # The detailed output is in the Ansible execution, not in result.messages
        # result.messages only contains high-level status messages
        assert len(result.messages) > 0, "Should have status messages"

        print(
            f"\n✅ E2E test completed - venv '{venv_name}' created and tested "
            "on night2.lan"
        )
        print("📦 Playbook executed successfully in remote venv")
        print("📊 Metadata collected from remote venv")

    def test_e2e_use_existing_persistent_venv(self, ssh_check, paths):
        """E2E test: Use existing persistent venv (should detect it exists)."""
        venv_name = "e2e_existing_venv"

        # Create metadata for "existing" venv
        existing_metadata = {
            "venv_name": venv_name,
            "target_host": "night2.lan",
            "persistent": True,
            "created_at": "2024-01-01 10:00:00",
        }
        save_venv_metadata(paths["metadata_dir"], venv_name, existing_metadata)

        result = run_playbook_with_venv(
            venv_wrapper_playbook_path=paths["venv_wrapper"],
            inventory_path=paths["inventory"],
            ssh_key_path=paths["ssh_key"],
            metadata_dir_path=paths["metadata_dir"],
            playbook_path=paths["hello_world"],
            target_host="night2.lan",
            persist=True,
            venv_name=venv_name,
        )

        # Should succeed and show existing venv usage
        assert result.success is True
        assert result.result_code == 0
        assert any("Using existing venv" in msg for msg in result.messages)
        assert result.existing_metadata["venv_name"] == venv_name

        print(f"\n✅ E2E existing venv test completed - used '{venv_name}'")

    def test_e2e_temporary_venv_cleanup(self, ssh_check, paths):
        """E2E test: Create temporary venv and verify it's not saved to metadata."""
        result = run_playbook_with_venv(
            venv_wrapper_playbook_path=paths["venv_wrapper"],
            inventory_path=paths["inventory"],
            ssh_key_path=paths["ssh_key"],
            metadata_dir_path=paths["metadata_dir"],
            playbook_path=paths["hello_world"],
            target_host="night2.lan",
            persist=False,  # Temporary venv
            venv_name=None,  # Auto-generate temp name
            extra_vars={"ansible_user": "mtm"},
        )

        # Should succeed with temp venv
        assert result.success is True
        assert result.result_code == 0
        assert result.venv_name.startswith("temp_")

        # Temporary venv should NOT be saved to persistent metadata
        temp_metadata = load_venv_metadata(
            paths["metadata_dir"], result.venv_name, "night2.lan"
        )
        assert temp_metadata is None, "Temporary venv should not be saved to metadata"

        print(
            f"\n✅ E2E temporary venv test completed - "
            f"'{result.venv_name}' not persisted"
        )

    def test_e2e_real_playbook_execution(self, ssh_check, paths):
        """E2E test: Execute actual hello_world.yml playbook in venv."""
        venv_name = "e2e_playbook_test"

        # Clean up any existing metadata
        delete_venv_metadata(paths["metadata_dir"], venv_name, "night2.lan")

        result = run_playbook_with_venv(
            venv_wrapper_playbook_path=paths["venv_wrapper"],
            inventory_path=paths["inventory"],
            ssh_key_path=paths["ssh_key"],
            metadata_dir_path=paths["metadata_dir"],
            playbook_path=paths["hello_world"],
            target_host="night2.lan",
            persist=True,
            venv_name=venv_name,
        )

        # Should succeed with real playbook execution
        assert result.success is True
        assert result.result_code == 0

        print(
            "\n✅ E2E playbook execution test completed - "
            "hello_world.yml ran in venv"
        )

    @pytest.fixture(scope="class", autouse=True)
    def cleanup_test_venvs(self, paths):
        """Clean up test venvs on remote host after all tests complete."""
        yield  # Run all tests first

        # Cleanup after tests
        try:
            subprocess.run(
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
                    "shell",
                    "-a",
                    "rm -rf ~/ansible-venvs/e2e_*",
                ],
                capture_output=True,
                timeout=30,
            )
            print("\n🧹 Cleaned up test venvs on night2.lan")
        except Exception as e:
            print(f"\n⚠️  Cleanup warning: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
