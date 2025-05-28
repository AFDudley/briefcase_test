"""
Ansible ping test functions for briefcase_ansible_test

This module contains functions for testing connectivity to Ansible hosts.
"""

import os
import sys
import traceback

from ansible.parsing.dataloader import DataLoader
from ansible.executor.task_queue_manager import TaskQueueManager

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
)
from .play_executor import create_play, load_play, execute_play_with_timeout


def ansible_ping_test(app, widget):
    """
    Run an Ansible ping module against the target host using the test SSH key.

    Args:
        app: The application instance
        widget: The widget that triggered this function
    """

    # Run in a background thread to keep UI responsive
    def run_in_background():
        try:
            # Target host configuration - use the group name to match inventory
            target_host = (
                "localhost"  # This matches the [localhost] group containing 127.0.0.1
            )

            # Get path to the SSH key
            key_path = os.path.join(
                app.paths.app, "resources", "keys", "briefcase_test_key"
            )

            # Path to the inventory file
            inventory_path = os.path.join(
                app.paths.app, "resources", "inventory", "sample_inventory.ini"
            )

            app.ui_updater.add_text_to_output(f"📁 Using inventory: {inventory_path}\n")

            # Setup Ansible objects
            loader = DataLoader()
            inventory, variable_manager = setup_ansible_inventory(
                inventory_path, loader
            )

            # Debug inventory contents
            debug_inventory_contents(
                inventory, target_host, app.ui_updater.add_text_to_output
            )

            # Configure Ansible context
            configure_ansible_context(key_path)

            # Check multiprocessing availability
            check_multiprocessing_availability(app.ui_updater.add_text_to_output)

            # Initialize plugin loader
            initialize_plugin_loader(app.ui_updater.add_text_to_output)

            # Check directory access and set up temp directory
            app.ui_updater.add_text_to_output("Checking directory access...\n")
            home_dir = os.path.expanduser("~")
            app.ui_updater.add_text_to_output(f"Home directory: {home_dir}\n")

            writable_dir, test_results = find_writable_directory(app)

            # Display test results
            for test_dir, success, error in test_results:
                if success:
                    app.ui_updater.add_text_to_output(
                        f"✅ Write access to: {test_dir}\n"
                    )
                else:
                    app.ui_updater.add_text_to_output(
                        f"❌ No write access to {test_dir}: {error}\n"
                    )

            # Set up Ansible temp directory
            if writable_dir:
                setup_ansible_temp_directory(
                    writable_dir, app.ui_updater.add_text_to_output
                )
            else:
                app.ui_updater.add_text_to_output("❌ No writable directory found!\n")

            # Create play
            play_source = create_play(target_host)
            play = load_play(
                play_source, variable_manager, loader, app.ui_updater.add_text_to_output
            )

            if not play:
                return

            # Create callback for output
            results_callback = SimpleCallback(app.ui_updater.add_text_to_output)

            # Run it with debugging
            tqm = None
            try:
                app.ui_updater.add_text_to_output("Creating TaskQueueManager...\n")
                tqm = TaskQueueManager(
                    inventory=inventory,
                    variable_manager=variable_manager,
                    loader=loader,
                    passwords=dict(),
                    stdout_callback=results_callback,
                    forks=1,
                )

                app.ui_updater.add_text_to_output("Running playbook...\n")

                try:
                    result = execute_play_with_timeout(
                        tqm, play, app.ui_updater.add_text_to_output
                    )
                except Exception as e:
                    app.ui_updater.add_text_to_output(f"❌ TQM.run() failed: {e}\n")
                    app.ui_updater.add_text_to_output(f"Exception type: {type(e)}\n")
                    app.ui_updater.add_text_to_output(
                        f"Traceback: {traceback.format_exc()}\n"
                    )
                    result = 1

                # Check if any hosts were processed
                if hasattr(results_callback, "host_ok"):
                    app.ui_updater.add_text_to_output(
                        f"Successful hosts: {len(getattr(results_callback, 'host_ok', {}))}\n"
                    )
                if hasattr(results_callback, "host_failed"):
                    app.ui_updater.add_text_to_output(
                        f"Failed hosts: {len(getattr(results_callback, 'host_failed', {}))}\n"
                    )
                if hasattr(results_callback, "host_unreachable"):
                    app.ui_updater.add_text_to_output(
                        f"Unreachable hosts: {len(getattr(results_callback, 'host_unreachable', {}))}\n"
                    )

                if result == 0:
                    app.ui_updater.add_text_to_output(
                        "✅ Ansible ping test completed successfully!\n"
                    )
                else:
                    app.ui_updater.add_text_to_output(
                        f"❌ Ansible ping test failed with result: {result}\n"
                    )

            finally:
                if tqm is not None:
                    tqm.cleanup()
                    app.ui_updater.add_text_to_output("🧹 Cleanup completed\n")

        except Exception as e:
            app.ui_updater.add_text_to_output(
                f"❌ Error during Ansible ping test: {e}\n"
            )
            app.ui_updater.add_text_to_output(f"Traceback: {traceback.format_exc()}\n")

    # Run the task in a background thread
    app.background_task_runner.run_task(
        run_in_background, "Running Ansible ping test..."
    )
