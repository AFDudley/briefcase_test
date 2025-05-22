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
    Run the sample Ansible playbook using Paramiko for SSH connections.

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

            app.ui_updater.add_text_to_output(
                "Loading inventory: sample_inventory.ini\n"
            )
            app.ui_updater.add_text_to_output("Loading playbook: sample_playbook.yml\n")

            # Create data loader
            loader = DataLoader()

            # Set up inventory
            inventory = InventoryManager(loader=loader, sources=[inventory_file])

            # Set up variable manager
            from ansible.vars.manager import VariableManager

            variable_manager = VariableManager(loader=loader, inventory=inventory)

            # Configure connection to use paramiko
            app.ui_updater.add_text_to_output(
                "Configuring Ansible to use Paramiko SSH connections\n"
            )

            # Define a subclass of CallbackBase to capture output
            from ansible.plugins.callback import CallbackBase

            class ResultCallback(CallbackBase):
                def __init__(self, output_callback):
                    super(ResultCallback, self).__init__()
                    self.output_callback = output_callback

                def v2_runner_on_ok(self, result):
                    host = result._host.get_name()
                    task = result._task.get_name()
                    self.output_callback(f"✅ {host} | {task} => SUCCESS\n")
                    if "msg" in result._result:
                        self.output_callback(f"   Message: {result._result['msg']}\n")

                def v2_runner_on_failed(self, result, ignore_errors=False):
                    host = result._host.get_name()
                    task = result._task.get_name()
                    self.output_callback(f"❌ {host} | {task} => FAILED\n")
                    if "msg" in result._result:
                        self.output_callback(f"   Error: {result._result['msg']}\n")

                def v2_runner_on_unreachable(self, result):
                    host = result._host.get_name()
                    self.output_callback(f"🔌 {host} => UNREACHABLE\n")

                def v2_playbook_on_play_start(self, play):
                    name = play.get_name()
                    self.output_callback(f"▶️ Starting play: {name}\n")

                def v2_playbook_on_task_start(self, task, is_conditional):
                    name = task.get_name()
                    self.output_callback(f"⏳ Running task: {name}\n")

            # Create a custom callback to receive events
            results_callback = ResultCallback(app.ui_updater.add_text_to_output)

            # Import necessary modules
            from ansible.executor.playbook_executor import PlaybookExecutor
            from ansible import context
            from ansible.utils.context_objects import ImmutableDict

            # Set context.CLIARGS which PlaybookExecutor will use internally
            context.CLIARGS = ImmutableDict(
                connection="paramiko",  # Use paramiko for SSH connections
                module_path=None,
                forks=1,  # Run tasks serially
                become=None,
                become_method=None,
                become_user=None,
                check=False,  # Don't perform a dry-run
                syntax=False,  # Don't just check syntax
                diff=False,  # Don't show file diffs
                verbosity=0,  # Minimal output
                listhosts=False,
                listtasks=False,
                listtags=False,
                ssh_common_args="",
                ssh_extra_args="",
                sftp_extra_args="",
                scp_extra_args="",
                become_ask_pass=False,
                remote_user=None,
                host_key_checking=False,  # Disable host key checking
            )

            app.ui_updater.add_text_to_output("Setting up playbook executor...\n")

            # Create playbook executor without passing options directly
            pbex = PlaybookExecutor(
                playbooks=[playbook_file],
                inventory=inventory,
                variable_manager=variable_manager,
                loader=loader,
                passwords={},
            )

            # Register our callback if _tqm is available
            if pbex._tqm is not None:
                pbex._tqm._stdout_callback = results_callback

            app.ui_updater.add_text_to_output(
                "Starting playbook execution with Paramiko transport...\n\n"
            )

            # Run the playbook
            result = pbex.run()

            if result == 0:
                app.ui_updater.add_text_to_output(
                    "\n✨ Playbook execution completed successfully.\n"
                )
                app.ui_updater.update_status("Completed")
            else:
                app.ui_updater.add_text_to_output(
                    f"\n⚠️ Playbook execution failed with code {result}.\n"
                )
                app.ui_updater.update_status("Failed")

        except Exception as error:
            # Handle any exceptions
            error_message = str(error)
            app.ui_updater.add_text_to_output(
                f"Error executing playbook: {error_message}"
            )
            app.ui_updater.update_status("Error")
            app.ui_updater.add_text_to_output(f"\nTraceback:\n{traceback.format_exc()}")

    # Run the task in a background thread
    app.background_task_runner.run_task(run_in_background, "Running sample playbook...")
