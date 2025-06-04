#!/usr/bin/env python3
"""
End-to-end tests for venv_management executor.py functions.

Tests all functions by calling run_playbook_with_venv in different ways.
"""

import os
import sys
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Mock iOS dependencies before importing
sys.modules['ios_multiprocessing'] = MagicMock()
sys.modules['rubicon'] = MagicMock()
sys.modules['rubicon.objc'] = MagicMock()

# Import the main function we'll test
from briefcase_ansible_test.ansible.venv_management.executor import run_playbook_with_venv
from briefcase_ansible_test.ansible.venv_management.metadata import (
    save_venv_metadata,
    load_venv_metadata,
    list_all_venvs
)


class TestExecutorE2E:
    """End-to-end tests for executor.py via run_playbook_with_venv."""
    
    @pytest.fixture
    def mock_app(self):
        """Create a mock app with paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            app = MagicMock()
            app.paths.app = Path(temp_dir) / 'app'
            app.paths.app.mkdir(parents=True)
            
            # Create required directory structure
            playbook_dir = app.paths.app / 'ansible' / 'venv_management' / 'playbooks'
            playbook_dir.mkdir(parents=True)
            
            # Create a minimal test playbook
            test_playbook = playbook_dir / 'venv_wrapper.yml'
            test_playbook.write_text("""---
- name: Test venv wrapper
  hosts: localhost
  connection: local
  gather_facts: no
  tasks:
    - name: Test task
      debug:
        msg: "Test venv management"
""")
            
            # Create inventory
            inventory_dir = app.paths.app / 'resources' / 'inventory'
            inventory_dir.mkdir(parents=True)
            inventory_file = inventory_dir / 'sample_inventory.ini'
            inventory_file.write_text("[localhost]\nlocalhost ansible_connection=local")
            
            # Create keys directory
            keys_dir = app.paths.app / 'resources' / 'keys'
            keys_dir.mkdir(parents=True)
            key_file = keys_dir / 'briefcase_test_key'
            key_file.touch()
            
            # Create test playbook to run
            playbooks_dir = app.paths.app / 'resources' / 'playbooks'
            playbooks_dir.mkdir(parents=True)
            hello_playbook = playbooks_dir / 'hello.yml'
            hello_playbook.write_text("""---
- name: Hello
  hosts: localhost
  tasks:
    - debug:
        msg: "Hello from venv"
""")
            
            yield app
    
    @pytest.fixture
    def mock_ui_updater(self):
        """Create a mock UI updater."""
        ui = MagicMock()
        ui.add_text_to_output = MagicMock()
        return ui
    
    def test_temporary_venv_no_name(self, mock_app, mock_ui_updater):
        """Test with temporary venv and auto-generated name.
        
        This tests:
        - generate_temp_venv_name() - called when venv_name is None
        - get_venv_path() - called with persist=False
        - create_venv_vars() - with minimal params
        - create_ansible_context() - for localhost
        - create_default_metadata() - for temp venv
        """
        # Mock the actual playbook execution to avoid running Ansible
        import briefcase_ansible_test.ansible.venv_management.executor as executor
        original_run = executor.run_venv_wrapper_playbook
        executor.run_venv_wrapper_playbook = MagicMock(return_value={
            "success": True,
            "venv_metadata": {
                "venv_name": "temp_12345",
                "venv_path": "/tmp/ansible-venv-temp_12345",
                "target_host": "localhost",
                "created_at": "2024-01-01 10:00:00",
                "persistent": False
            },
            "result_code": 0
        })
        
        try:
            result = run_playbook_with_venv(
                mock_app,
                playbook_path="/path/to/playbook.yml",
                target_host="localhost",
                persist=False,
                venv_name=None,  # Forces generate_temp_venv_name()
                ui_updater=mock_ui_updater
            )
            
            assert result is True
            
            # Verify the generated name pattern
            call_args = executor.run_venv_wrapper_playbook.call_args[0][1]
            assert call_args['venv_name'].startswith('temp_')
            assert call_args['venv_path'].startswith('/tmp/ansible-venv-temp_')
            assert call_args['persist_venv'] is False
            assert call_args['target_host'] == 'localhost'
            
        finally:
            executor.run_venv_wrapper_playbook = original_run
    
    def test_persistent_venv_with_existing(self, mock_app, mock_ui_updater):
        """Test with persistent venv that already exists.
        
        This tests:
        - load_venv_metadata() - checking for existing venv
        - get_venv_path() - called with persist=True
        - create_venv_vars() - with all params
        - Message formatting for existing venv
        """
        # Create existing metadata
        existing_metadata = {
            "venv_name": "prod_venv",
            "venv_path": "~/ansible-venvs/prod_venv",
            "target_host": "server1",
            "persistent": True,
            "created_at": "2024-01-01 09:00:00"
        }
        save_venv_metadata(mock_app.paths, "prod_venv", existing_metadata)
        
        # Mock the playbook execution
        import briefcase_ansible_test.ansible.venv_management.executor as executor
        original_run = executor.run_venv_wrapper_playbook
        executor.run_venv_wrapper_playbook = MagicMock(return_value={
            "success": True,
            "venv_metadata": existing_metadata,
            "result_code": 0
        })
        
        try:
            result = run_playbook_with_venv(
                mock_app,
                playbook_path="/path/to/playbook.yml",
                target_host="server1",
                persist=True,
                venv_name="prod_venv",
                collections=["community.general", "ansible.posix"],
                python_packages=["ansible-core", "paramiko"],
                extra_vars={"api_key": "secret"},
                ui_updater=mock_ui_updater
            )
            
            assert result is True
            
            # Verify existing venv message was shown
            mock_ui_updater.add_text_to_output.assert_any_call(
                "Using existing venv 'prod_venv' created at 2024-01-01 09:00:00\n"
            )
            
            # Verify all parameters were passed correctly
            call_args = executor.run_venv_wrapper_playbook.call_args[0][1]
            assert call_args['venv_name'] == 'prod_venv'
            assert call_args['venv_path'] == '~/ansible-venvs/prod_venv'
            assert call_args['persist_venv'] is True
            assert call_args['ansible_collections'] == ["community.general", "ansible.posix"]
            assert call_args['python_packages'] == ["ansible-core", "paramiko"]
            assert call_args['api_key'] == 'secret'
            
        finally:
            executor.run_venv_wrapper_playbook = original_run
    
    def test_failed_execution(self, mock_app, mock_ui_updater):
        """Test handling of failed execution.
        
        This tests:
        - Metadata is NOT saved on failure
        - Return value is False
        """
        import briefcase_ansible_test.ansible.venv_management.executor as executor
        original_run = executor.run_venv_wrapper_playbook
        executor.run_venv_wrapper_playbook = MagicMock(return_value={
            "success": False,
            "venv_metadata": None,
            "result_code": 1
        })
        
        try:
            result = run_playbook_with_venv(
                mock_app,
                playbook_path="/path/to/playbook.yml",
                target_host="localhost",
                venv_name="failing_venv",
                ui_updater=mock_ui_updater
            )
            
            assert result is False
            
            # Verify metadata was NOT saved
            loaded = load_venv_metadata(mock_app.paths, "failing_venv", "localhost")
            assert loaded is None
            
            # Verify no success message
            for call in mock_ui_updater.add_text_to_output.call_args_list:
                assert "✅ Metadata saved" not in call[0][0]
                
        finally:
            executor.run_venv_wrapper_playbook = original_run
    
    def test_all_parameters_flow_through(self, mock_app, mock_ui_updater):
        """Test that all parameters flow through the function chain correctly.
        
        This verifies the integration of:
        - create_venv_vars() receiving all inputs
        - create_ansible_context() with SSH for remote host
        - create_default_metadata() with all fields
        """
        import briefcase_ansible_test.ansible.venv_management.executor as executor
        
        # Track what gets passed to run_venv_wrapper_playbook
        captured_vars = {}
        
        def capture_vars(app, wrapper_vars, ui_updater):
            captured_vars.update(wrapper_vars)
            return {
                "success": True,
                "venv_metadata": {
                    "venv_name": wrapper_vars['venv_name'],
                    "venv_path": wrapper_vars['venv_path'],
                    "target_host": wrapper_vars['target_host'],
                    "created_at": "2024-01-01 10:00:00",
                    "persistent": wrapper_vars['persist_venv']
                },
                "result_code": 0
            }
        
        original_run = executor.run_venv_wrapper_playbook
        executor.run_venv_wrapper_playbook = capture_vars
        
        try:
            result = run_playbook_with_venv(
                mock_app,
                playbook_path="/custom/playbook.yml",
                target_host="remote.server.com",  # Non-localhost to test SSH context
                persist=True,
                venv_name="custom_venv",
                collections=["custom.collection"],
                python_packages=["custom-package", "ansible-core"],
                extra_vars={"custom_var": "custom_value", "debug": True},
                ui_updater=mock_ui_updater
            )
            
            assert result is True
            
            # Verify all parameters made it through
            assert captured_vars['venv_name'] == 'custom_venv'
            assert captured_vars['venv_path'] == '~/ansible-venvs/custom_venv'
            assert captured_vars['persist_venv'] is True
            assert captured_vars['target_host'] == 'remote.server.com'
            assert captured_vars['playbook_to_run'] == '/custom/playbook.yml'
            assert captured_vars['ansible_collections'] == ['custom.collection']
            assert captured_vars['python_packages'] == ['custom-package', 'ansible-core']
            assert captured_vars['custom_var'] == 'custom_value'
            assert captured_vars['debug'] is True
            assert captured_vars['collect_metadata'] is True
            
            # Verify metadata was saved
            saved = load_venv_metadata(mock_app.paths, "custom_venv", "remote.server.com")
            assert saved is not None
            assert saved['venv_name'] == 'custom_venv'
            assert saved['persistent'] is True
            
        finally:
            executor.run_venv_wrapper_playbook = original_run


if __name__ == '__main__':
    pytest.main([__file__, '-v'])