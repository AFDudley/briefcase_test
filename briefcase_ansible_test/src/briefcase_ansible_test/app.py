"""
A simple app to parse and display Ansible inventory using Ansible's InventoryManager
"""

# Standard library imports
import asyncio
import json
import os
import traceback

# Import ansible module first - its __init__.py will set up all required system mocks
import briefcase_ansible_test.ansible

# Third-party imports
import toga
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader

# Local application imports
from briefcase_ansible_test.ansible import parse_ansible_inventory
from briefcase_ansible_test.ssh_utils import test_ssh_connection
from briefcase_ansible_test.ui import BackgroundTaskRunner, UIComponents, UIUpdater


class BriefcaseAnsibleTest(toga.App):
    def __init__(self, *args, **kwargs):
        """Construct the Toga application."""
        super().__init__(*args, **kwargs)
        # Store a set for background tasks to prevent garbage collection
        self.background_tasks = set()

    def startup(self):
        """Initialize the application."""
        # Store a reference to the main event loop for background threads
        self.main_event_loop = asyncio.get_event_loop()
        # Define button configurations as tuples: (label, callback, tooltip)
        button_configs = [
            (
                "Parse Inventory",
                lambda widget: parse_ansible_inventory(self, widget),
                "Parse Ansible inventory files",
            ),
            (
                "Parse Playbook",
                self.parse_ansible_playbook,
                "Parse Ansible playbook files",
            ),
            (
                "Test Paramiko",
                self.test_paramiko_connection,
                "Test SSH connection using Paramiko",
            ),
            (
                "Run Playbook (Paramiko)",
                self.run_ansible_playbook,
                "Run Ansible playbook using Paramiko",
            ),
            ("Ansible Ping Test", self.ansible_ping_test, "Run Ansible ping test"),
        ]

        # Create action buttons using UIComponents
        action_buttons = UIComponents.create_action_buttons(self, button_configs)

        # Create output area and status label
        self.output_view, self.status_label = UIComponents.create_output_area()

        # Create UI updater and background task runner
        self.ui_updater = UIUpdater(
            self.output_view, self.status_label, self.main_event_loop
        )
        self.background_task_runner = BackgroundTaskRunner(self.ui_updater)

        # Make sure background_task_runner uses our task set
        self.background_task_runner.background_tasks = self.background_tasks

        # Create main layout with all components
        main_box = UIComponents.create_main_layout(
            "Ansible Inventory Viewer",
            action_buttons,
            self.output_view,
            self.status_label,
        )

        # Create and show the main window
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.size = (600, 400)
        self.main_window.show()

    # Using UIUpdater from ui.py for text and status updates

    def parse_ansible_playbook(self, widget):
        """Parse the sample ansible playbook file using Ansible's DataLoader."""

        def parse_playbook_task():
            # Path to the playbook file
            playbook_file = os.path.join(
                self.paths.app, "resources", "playbooks", "sample_playbook.yml"
            )

            self.ui_updater.add_text_to_output("Parsing file: sample_playbook.yml\n")

            # Use Ansible's data loader to parse the YAML file
            loader = DataLoader()

            # Load the playbook file
            playbook_data = loader.load_from_file(playbook_file)

            # Convert playbook data to JSON for display
            playbook_json = json.dumps(playbook_data, indent=2)

            # Update the UI with the parsed playbook
            self.ui_updater.add_text_to_output(f"Parsed data:\n{playbook_json}\n\n")

            # Final update when everything is done
            self.ui_updater.add_text_to_output(
                "Playbook parsing completed successfully.\n"
            )
            self.ui_updater.update_status("Completed")

        # Run the task in a background thread
        self.background_task_runner.run_task(parse_playbook_task, "Parsing playbook...")

    def test_paramiko_connection(self, widget):
        """Test a basic Paramiko SSH connection."""

        # Run in background to keep UI responsive
        def run_in_background():
            # Get path to the SSH key
            key_path = os.path.join(
                self.paths.app, "resources", "keys", "briefcase_test_key"
            )
            # Run the SSH test with our UI updater and the key path
            test_ssh_connection(
                "night2", "mtm", key_path=key_path, ui_updater=self.ui_updater
            )

        # Run the task in a background thread
        self.background_task_runner.run_task(
            run_in_background, "Testing Paramiko connection..."
        )

    def run_ansible_playbook(self, widget):
        """Run the sample Ansible playbook using Paramiko for SSH connections."""

        # Run in a background thread to keep UI responsive
        def run_in_background():
            try:
                # Path to the files
                inventory_file = os.path.join(
                    self.paths.app, "resources", "inventory", "sample_inventory.ini"
                )
                playbook_file = os.path.join(
                    self.paths.app, "resources", "playbooks", "sample_playbook.yml"
                )

                self.ui_updater.add_text_to_output(
                    "Loading inventory: sample_inventory.ini\n"
                )
                self.ui_updater.add_text_to_output(
                    "Loading playbook: sample_playbook.yml\n"
                )

                # Create data loader
                loader = DataLoader()

                # Set up inventory
                inventory = InventoryManager(loader=loader, sources=[inventory_file])

                # Set up variable manager
                from ansible.vars.manager import VariableManager

                variable_manager = VariableManager(loader=loader, inventory=inventory)

                # Configure connection to use paramiko
                self.ui_updater.add_text_to_output(
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
                            self.output_callback(
                                f"   Message: {result._result['msg']}\n"
                            )

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
                results_callback = ResultCallback(self.ui_updater.add_text_to_output)

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

                self.ui_updater.add_text_to_output("Setting up playbook executor...\n")

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

                self.ui_updater.add_text_to_output(
                    "Starting playbook execution with Paramiko transport...\n\n"
                )

                # Run the playbook
                result = pbex.run()

                if result == 0:
                    self.ui_updater.add_text_to_output(
                        "\n✨ Playbook execution completed successfully.\n"
                    )
                    self.ui_updater.update_status("Completed")
                else:
                    self.ui_updater.add_text_to_output(
                        f"\n⚠️ Playbook execution failed with code {result}.\n"
                    )
                    self.ui_updater.update_status("Failed")

            except Exception as error:
                # Handle any exceptions
                error_message = str(error)
                self.ui_updater.add_text_to_output(
                    f"Error executing playbook: {error_message}"
                )
                self.ui_updater.update_status("Error")

        # Run the task in a background thread
        self.background_task_runner.run_task(
            run_in_background, "Running sample playbook..."
        )

    def ansible_ping_test(self, widget):
        """Run an Ansible ping module against night2 to verify SSH connectivity."""

        # Run in a background thread to keep UI responsive
        def run_in_background():
            try:
                # Import Ansible modules
                from ansible.module_utils.common.collections import ImmutableDict
                from ansible.parsing.dataloader import DataLoader
                from ansible.inventory.manager import InventoryManager
                from ansible.vars.manager import VariableManager
                from ansible.playbook.play import Play
                from ansible.executor.task_queue_manager import TaskQueueManager
                from ansible.plugins.callback import CallbackBase
                from ansible import context

                # Define a custom callback to capture output
                class ResultCallback(CallbackBase):
                    def __init__(self, output_callback):
                        super(ResultCallback, self).__init__()
                        self.output_callback = output_callback
                        self.host_ok = {}
                        self.host_failed = {}
                        self.host_unreachable = {}

                    def v2_runner_on_ok(self, result):
                        host = result._host.get_name()
                        self.host_ok[host] = result
                        output = f"{host} | SUCCESS => {{\n"
                        output += f"    \"changed\": {str(result._result.get('changed', False)).lower()},\n"
                        if "ansible_facts" in result._result:
                            output += '    "ansible_facts": {\n'
                            for k, v in result._result["ansible_facts"].items():
                                output += (
                                    '        "' + str(k) + '": "' + str(v) + '",\n'
                                )
                            output += "    },\n"
                        output += (
                            '    "ping": "'
                            + str(result._result.get("ping", ""))
                            + '"\n'
                        )
                        output += "}\n"
                        self.output_callback(output)

                    def v2_runner_on_failed(self, result, ignore_errors=False):
                        host = result._host.get_name()
                        self.host_failed[host] = result
                        output = f"{host} | FAILED => {{\n"
                        output += (
                            '    "msg": "'
                            + str(result._result.get("msg", "unknown error"))
                            + '"\n'
                        )
                        output += "}\n"
                        self.output_callback(output)

                    def v2_runner_on_unreachable(self, result):
                        host = result._host.get_name()
                        self.host_unreachable[host] = result
                        output = host + " | UNREACHABLE => {\n"
                        output += (
                            '    "msg": "'
                            + str(result._result.get("msg", "unreachable"))
                            + '"\n'
                        )
                        output += "}\n"
                        self.output_callback(output)

                # Path to the inventory file
                inventory_file = os.path.join(
                    self.paths.app, "resources", "inventory", "sample_inventory.ini"
                )
                self.ui_updater.add_text_to_output(
                    "Using inventory: " + inventory_file + "\n"
                )
                self.ui_updater.add_text_to_output("Target: night2\n\n")

                # Setup Ansible objects
                loader = DataLoader()
                inventory = InventoryManager(loader=loader, sources=[inventory_file])
                variable_manager = VariableManager(loader=loader, inventory=inventory)

                # Create and configure options
                context.CLIARGS = ImmutableDict(
                    connection="ssh",
                    module_path=[],
                    forks=10,
                    become=None,
                    become_method=None,
                    become_user=None,
                    check=False,
                    diff=False,
                    verbosity=0,
                )

                # Create play with ping task
                play_source = dict(
                    name="Ansible Ping",
                    hosts="night2",
                    gather_facts=False,
                    tasks=[dict(action=dict(module="ping"))],
                )

                # Create the Play
                play = Play().load(
                    play_source, variable_manager=variable_manager, loader=loader
                )

                # Create callback for output
                results_callback = ResultCallback(self.ui_updater.add_text_to_output)

                # Run it
                tqm = None
                try:
                    tqm = TaskQueueManager(
                        inventory=inventory,
                        variable_manager=variable_manager,
                        loader=loader,
                        passwords=dict(),
                        stdout_callback=results_callback,
                    )
                    result = tqm.run(play)

                    if result == 0:
                        self.ui_updater.update_status("Success")
                    else:
                        self.ui_updater.update_status("Failed")

                finally:
                    if tqm is not None:
                        tqm.cleanup()

            except Exception as error:
                self.ui_updater.add_text_to_output(
                    f"Error running Ansible ping: {str(error)}\n"
                )
                self.ui_updater.add_text_to_output(
                    f"Traceback: {traceback.format_exc()}\n"
                )
                self.ui_updater.update_status("Error")

        # Run the task in a background thread
        self.background_task_runner.run_task(
            run_in_background, "Running Ansible ping test..."
        )


def main():
    # Return the app instance without calling main_loop()
    # The caller (e.g., __main__.py) will handle calling main_loop()
    return BriefcaseAnsibleTest()
