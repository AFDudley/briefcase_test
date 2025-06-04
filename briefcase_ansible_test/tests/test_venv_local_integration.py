#!/usr/bin/env python3
"""
Integration test for venv_management module.

Tests the complete lifecycle:
1. Create venv locally
2. Verify installation
3. Run hello_world.yml using the venv
4. Clean up venv
5. Verify deletion
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

# Import metadata functions directly to avoid iOS-specific imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'briefcase_ansible_test' / 'ansible' / 'venv_management'))
from metadata import (
    save_venv_metadata,
    load_venv_metadata,
    delete_venv_metadata,
    list_all_venvs
)


class TestVenvLocalIntegration:
    """Test venv creation, usage, and cleanup locally."""

    @pytest.fixture
    def temp_base_dir(self):
        """Create a temporary directory for venv testing."""
        temp_dir = tempfile.mkdtemp(prefix="venv_test_")
        yield temp_dir
        # Cleanup after test
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    def test_venv_lifecycle_simple(self, temp_base_dir):
        """Test venv lifecycle using direct commands instead of wrapper playbook."""
        # Create mock app paths for metadata functions
        class MockAppPaths:
            def __init__(self, base):
                self.app = Path(base) / 'app'
        
        app_paths = MockAppPaths(temp_base_dir)
        app_paths.app.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        venv_name = f"test_venv_{int(time.time())}"
        venv_path = Path(temp_base_dir) / venv_name
        hello_world = Path(__file__).parent.parent / 'src' / 'briefcase_ansible_test' / 'resources' / 'playbooks' / 'hello_world.yml'

        # 1. Create venv directly
        print(f"\nCreating venv at: {venv_path}")
        create_cmd = [sys.executable, '-m', 'venv', str(venv_path)]
        result = subprocess.run(create_cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"Venv creation failed:\n{result.stderr}"

        # 2. Verify venv exists
        assert venv_path.exists(), f"Venv not created at {venv_path}"

        # Get python executable path
        python_exe = venv_path / 'bin' / 'python'
        pip_exe = venv_path / 'bin' / 'pip'

        assert python_exe.exists(), f"Python executable not found at {python_exe}"

        # 3. Install ansible in venv
        print("\nInstalling ansible in venv")
        install_cmd = [str(pip_exe), 'install', 'ansible-core']
        result = subprocess.run(install_cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"Ansible installation failed:\n{result.stderr}"

        # Verify ansible is installed
        ansible_exe = venv_path / ('Scripts' if os.name == 'nt' else 'bin') / 'ansible-playbook'
        assert ansible_exe.exists(), f"ansible-playbook not found at {ansible_exe}"

        # 4. Run hello_world.yml using the venv's ansible
        print(f"\nExecuting hello_world.yml using venv")
        execute_cmd = [
            str(ansible_exe),
            str(hello_world),
            '-i', 'localhost,',
            '-c', 'local'
        ]

        result = subprocess.run(execute_cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"Playbook execution failed:\n{result.stderr}\n{result.stdout}"

        # Verify output
        assert "Hello, World from Ansible!" in result.stdout, "Hello world message not found"
        assert "Hello from iOS!" in result.stdout, "Custom greeting not found"

        # 5. Use metadata module to save venv metadata
        metadata = {
            "venv_name": venv_name,
            "venv_path": str(venv_path),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "target_host": "localhost",
            "persistent": False,
            "python_version": subprocess.check_output([str(python_exe), '--version'], text=True).strip(),
            "ansible_version": subprocess.check_output([str(ansible_exe), '--version'], text=True).split('\n')[0]
        }

        # Save metadata using the module function
        saved_path = save_venv_metadata(app_paths, venv_name, metadata)
        print(f"\nMetadata saved to: {saved_path}")
        
        # Verify metadata was saved and can be loaded
        loaded_metadata = load_venv_metadata(app_paths, venv_name, "localhost")
        assert loaded_metadata is not None, "Failed to load metadata"
        assert loaded_metadata['venv_name'] == venv_name
        assert loaded_metadata['target_host'] == "localhost"
        assert 'metadata_version' in loaded_metadata  # Added by enrich_metadata
        assert 'last_updated' in loaded_metadata  # Added by enrich_metadata

        # 6. Clean up venv
        print(f"\nCleaning up venv")
        shutil.rmtree(venv_path)

        # 7. Verify venv cleanup
        assert not venv_path.exists(), f"Venv still exists at {venv_path}"

        # Clean up metadata using the module function
        deleted = delete_venv_metadata(app_paths, venv_name, "localhost")
        assert deleted, "Failed to delete metadata"
        
        # Verify metadata is deleted
        reloaded_metadata = load_venv_metadata(app_paths, venv_name, "localhost")
        assert reloaded_metadata is None, "Metadata file still exists after deletion"

        print("\nVenv lifecycle test completed successfully!")
    
    def test_list_all_venvs(self, temp_base_dir):
        """Test listing multiple venvs."""
        # Create mock app paths
        class MockAppPaths:
            def __init__(self, base):
                self.app = Path(base) / 'app'
        
        app_paths = MockAppPaths(temp_base_dir)
        app_paths.app.mkdir(parents=True, exist_ok=True)
        
        # Initially should be empty
        venvs = list_all_venvs(app_paths)
        assert len(venvs) == 0, "Should start with no venvs"
        
        # Save metadata for 3 different venvs
        metadata1 = {
            "venv_name": "test_venv_1",
            "venv_path": "/tmp/test_venv_1",
            "target_host": "localhost",
            "persistent": False,
            "created_at": "2024-01-01 10:00:00"
        }
        save_venv_metadata(app_paths, "test_venv_1", metadata1)
        
        metadata2 = {
            "venv_name": "prod_venv",
            "venv_path": "/home/user/venvs/prod_venv",
            "target_host": "server1.example.com",
            "persistent": True,
            "created_at": "2024-01-02 11:00:00"
        }
        save_venv_metadata(app_paths, "prod_venv", metadata2)
        
        metadata3 = {
            "venv_name": "ansible_venv",
            "venv_path": "/tmp/ansible_venv",
            "target_host": "localhost",
            "persistent": False,
            "created_at": "2024-01-03 12:00:00"
        }
        save_venv_metadata(app_paths, "ansible_venv", metadata3)
        
        # List all venvs
        venvs = list_all_venvs(app_paths)
        assert len(venvs) == 3, f"Expected 3 venvs, got {len(venvs)}"
        
        # Verify all venvs are present
        venv_names = {v['venv_name'] for v in venvs}
        assert venv_names == {"test_venv_1", "prod_venv", "ansible_venv"}
        
        # Verify enriched fields are present
        for venv in venvs:
            assert 'last_updated' in venv, "Missing last_updated field"
            assert 'metadata_version' in venv, "Missing metadata_version field"
        
        # Delete one and verify list updates
        delete_venv_metadata(app_paths, "test_venv_1", "localhost")
        venvs = list_all_venvs(app_paths)
        assert len(venvs) == 2, f"Expected 2 venvs after deletion, got {len(venvs)}"
        
        remaining_names = {v['venv_name'] for v in venvs}
        assert remaining_names == {"prod_venv", "ansible_venv"}
        
        # Clean up
        delete_venv_metadata(app_paths, "prod_venv", "server1.example.com")
        delete_venv_metadata(app_paths, "ansible_venv", "localhost")
        
        print("\nList all venvs test completed successfully!")


if __name__ == '__main__':
    import sys
    pytest.main([__file__, '-v'])
