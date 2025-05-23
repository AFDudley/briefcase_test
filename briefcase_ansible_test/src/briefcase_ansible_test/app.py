"""
A simple app to parse and display Ansible inventory using Ansible's InventoryManager
"""

# Standard library imports
import os
import asyncio

# Third-party imports
import toga

# Local application imports
from briefcase_ansible_test.ansible import (
    parse_ansible_inventory,
    parse_ansible_playbook,
    run_ansible_playbook,
    ansible_ping_test,
)
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
        # Import test functions
        from .test_multiprocessing import test_multiprocessing
        from .test_worker_import import test_worker_import
        from .test_display_import import test_display_import
        from .test_task_executor_imports import test_task_executor_imports
        from .test_direct_import import test_direct_import
        from .test_module_level_sim import test_module_level_sim
        from .test_import_trace import test_import_trace
        from .test_ansible_workerprocess import test_ansible_workerprocess
        from .test_simple_workerprocess import test_simple_workerprocess
        from .test_ssh_connection import test_ssh_connection

        # Define button configurations as tuples: (label, callback, tooltip)
        button_configs = [
            # (
            #     "Parse Inventory",
            #     lambda widget: parse_ansible_inventory(self, widget),
            #     "Parse Ansible inventory files",
            # ),
            # (
            #     "Parse Playbook",
            #     lambda widget: parse_ansible_playbook(self, widget),
            #     "Parse Ansible playbook files",
            # ),
            # (
            #     "Test Paramiko",
            #     self.test_paramiko_connection,
            #     "Test SSH connection using Paramiko",
            # ),
            # (
            #     "Run Playbook (Paramiko)",
            #     lambda widget: run_ansible_playbook(self, widget),
            #     "Run Ansible playbook using Paramiko",
            # ),
            (
                "Local Ansible Ping Test",
                lambda widget: ansible_ping_test(self, widget),
                "Run Ansible ping test",
            ),
            (
                "Test Import Trace",
                lambda widget: self.background_task_runner.run_task(
                    lambda: test_import_trace(self.ui_updater), "Tracing imports..."
                ),
                "Trace imports to find circular dependencies",
            ),
            (
                "Test Module Level Sim",
                lambda widget: self.background_task_runner.run_task(
                    lambda: test_module_level_sim(self.ui_updater),
                    "Testing module level simulation...",
                ),
                "Simulate task_executor module-level code",
            ),
            (
                "Test WorkerProcess",
                lambda widget: self.background_task_runner.run_task(
                    lambda: test_ansible_workerprocess(self.ui_updater),
                    "Testing Ansible WorkerProcess...",
                ),
                "Test Ansible's actual WorkerProcess in isolation",
            ),
            (
                "Simple WorkerProcess Test",
                lambda widget: self.background_task_runner.run_task(
                    lambda: test_simple_workerprocess(self.ui_updater),
                    "Testing Simple WorkerProcess...",
                ),
                "Test WorkerProcess with minimal dependencies",
            ),
            (
                "Test SSH Connection",
                lambda widget: self.background_task_runner.run_task(
                    lambda: test_ssh_connection(self.ui_updater),
                    "Testing SSH Connection...",
                ),
                "Test direct SSH connection to 127.0.0.1",
            ),
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
            "Ansible Test Runner",
            action_buttons,
            self.output_view,
            self.status_label,
        )

        # Create and show the main window
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.size = (600, 400)
        self.main_window.show()

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


def main():
    return BriefcaseAnsibleTest()
