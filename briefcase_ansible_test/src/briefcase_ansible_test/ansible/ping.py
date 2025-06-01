"""
Ansible ping test functions for briefcase_ansible_test

This module contains functions for testing connectivity to Ansible hosts.
"""

import os
import traceback

from ansible.parsing.dataloader import DataLoader

from .callbacks import SimpleCallback
from .inventory_debug import debug_inventory_contents
from .ios_setup import (
    check_multiprocessing_availability,
    find_writable_directory,
    setup_ansible_temp_directory,
)
from .ansible_config import (
    configure_ansible_context,
    initialize_plugin_loader,
    setup_ansible_inventory,
    ansible_task_queue_manager,
)
from .play_executor import load_play, execute_play_with_timeout
from ..utils.data_processing import build_ansible_play_dict


def ansible_ping_test(app, widget):
    """Run Ansible ping against localhost."""
    def run_in_background():
        ui = app.ui_updater.add_text_to_output
        paths = app.paths.app
        
        # Setup paths
        key_path = os.path.join(paths, "resources/keys/briefcase_test_key")
        inventory_path = os.path.join(paths, "resources/inventory/sample_inventory.ini")
        
        # Setup Ansible
        loader = DataLoader()
        inventory, variable_manager = setup_ansible_inventory(inventory_path, loader)
        configure_ansible_context(key_path)
        
        # Check iOS requirements
        check_multiprocessing_availability(ui)
        initialize_plugin_loader(ui)
        
        writable_dir, _ = find_writable_directory(app)
        if not writable_dir:
            ui("❌ No writable directory found!\n")
            return
            
        setup_ansible_temp_directory(writable_dir, ui)
        
        # Create and load play
        play = load_play(
            build_ansible_play_dict("localhost", task_module="ping"), 
            variable_manager, 
            loader, 
            ui
        )
        if not play:
            return
        
        # Execute with TQM
        results_callback = SimpleCallback(ui)
        
        with ansible_task_queue_manager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            stdout_callback=results_callback,
            forks=1,
        ) as tqm:
            result = execute_play_with_timeout(tqm, play, ui)
            
            # Report results
            ui(f"Successful hosts: {len(getattr(results_callback, 'host_ok', {}))}\n")
            ui(f"Failed hosts: {len(getattr(results_callback, 'host_failed', {}))}\n")
            
            status = "✅ completed successfully" if result == 0 else f"❌ failed: {result}"
            ui(f"Ansible ping test {status}!\n")
        
        ui("🧹 Cleanup completed\n")
    
    app.background_task_runner.run_task(run_in_background, "Running Ansible ping test...")
