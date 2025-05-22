"""
Ansible playbook functions for briefcase_ansible_test

This module contains functions for parsing and manipulating Ansible playbooks.
"""

import os
import json
import traceback

# Import Ansible modules
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager


def parse_ansible_playbook(app, widget):
    """
    Parse the sample ansible playbook file using Ansible's DataLoader.

    Args:
        app: The application instance
        widget: The widget that triggered this function
    """

    def parse_playbook_task():
        # Path to the playbook file
        playbook_file = os.path.join(
            app.paths.app, "resources", "playbooks", "sample_playbook.yml"
        )

        app.ui_updater.add_text_to_output("Parsing file: sample_playbook.yml\n")

        # Use Ansible's data loader to parse the YAML file
        loader = DataLoader()

        # Load the playbook file
        playbook_data = loader.load_from_file(playbook_file)

        # Convert playbook data to JSON for display
        playbook_json = json.dumps(playbook_data, indent=2)

        # Update the UI with the parsed playbook
        app.ui_updater.add_text_to_output(f"Parsed data:\n{playbook_json}\n\n")

        # Final update when everything is done
        app.ui_updater.add_text_to_output("Playbook parsing completed successfully.\n")
        app.ui_updater.update_status("Completed")

    # Run the task in a background thread
    app.background_task_runner.run_task(parse_playbook_task, "Parsing playbook...")


def run_ansible_playbook(app, widget):
    """
    Run the sample Ansible playbook using a simplified Play-based approach.

    Args:
        app: The application instance
        widget: The widget that triggered this function
    """

    # Run in a background thread to keep UI responsive
    def run_in_background():
        try:
            # Path to the files
            inventory_file = os.path.join(
                app.paths.app, "resources", "inventory", "sample_inventory.ini"
            )
            playbook_file = os.path.join(
                app.paths.app, "resources", "playbooks", "sample_playbook.yml"
            )

            app.ui_updater.add_text_to_output("Loading inventory and playbook...\n")

            # Create data loader and load playbook
            loader = DataLoader()
            playbook_data = loader.load_from_file(playbook_file)
            
            # Set up inventory and variable manager
            inventory = InventoryManager(loader=loader, sources=[inventory_file])
            from ansible.vars.manager import VariableManager
            variable_manager = VariableManager(loader=loader, inventory=inventory)

            app.ui_updater.add_text_to_output("Setting up Ansible context...\n")

            # Import necessary modules
            from ansible.playbook.play import Play
            from ansible.executor.task_queue_manager import TaskQueueManager
            from ansible.plugins.callback import CallbackBase
            from ansible import context
            from ansible.module_utils.common.collections import ImmutableDict

            # Set up context for serial execution
            context.CLIARGS = ImmutableDict(
                connection="paramiko",
                module_path=[],
                forks=1,
                become=None,
                become_method=None,
                become_user=None,
                check=False,
                diff=False,
                verbosity=0,
                host_key_checking=False,
            )

            # Simple callback for output
            class SimpleCallback(CallbackBase):
                def __init__(self, output_callback):
                    super().__init__()
                    self.output_callback = output_callback

                def v2_runner_on_ok(self, result):
                    host = result._host.get_name()
                    task = result._task.get_name()
                    self.output_callback(f"✅ {host} | {task} => SUCCESS\n")

                def v2_runner_on_failed(self, result, ignore_errors=False):
                    host = result._host.get_name()
                    task = result._task.get_name()
                    self.output_callback(f"❌ {host} | {task} => FAILED\n")

            # Create Play from playbook data (use first play)
            if isinstance(playbook_data, list) and playbook_data:
                play_data = playbook_data[0]
            else:
                play_data = playbook_data

            play = Play().load(play_data, variable_manager=variable_manager, loader=loader)
            
            app.ui_updater.add_text_to_output(f"Running play: {play.get_name()}\n")

            # Execute the play
            tqm = None
            try:
                callback = SimpleCallback(app.ui_updater.add_text_to_output)
                tqm = TaskQueueManager(
                    inventory=inventory,
                    variable_manager=variable_manager,
                    loader=loader,
                    passwords={},
                    stdout_callback=callback,
                )
                result = tqm.run(play)

                if result == 0:
                    app.ui_updater.add_text_to_output("✨ Playbook completed successfully!\n")
                    app.ui_updater.update_status("Completed")
                else:
                    app.ui_updater.add_text_to_output(f"⚠️ Playbook failed with code {result}\n")
                    app.ui_updater.update_status("Failed")

            finally:
                if tqm is not None:
                    tqm.cleanup()

        except Exception as error:
            app.ui_updater.add_text_to_output(f"Error: {str(error)}\n")
            app.ui_updater.add_text_to_output(f"Traceback:\n{traceback.format_exc()}")
            app.ui_updater.update_status("Error")

    # Run the task in a background thread
    app.background_task_runner.run_task(run_in_background, "Running playbook...")
