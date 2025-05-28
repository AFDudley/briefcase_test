"""
A simple app to parse and display Ansible inventory using Ansible's InventoryManager
"""

# Standard library imports
import os
import asyncio

# Third-party imports
import toga

# Local application imports
from briefcase_ansible_test.ssh_utils import test_ssh_connection, generate_ed25519_key, test_ssh_connection_with_generated_key
from briefcase_ansible_test.ui import BackgroundTaskRunner, UIComponents, UIUpdater
from briefcase_ansible_test.utils.logging import setup_app_logging, AppLogger
from briefcase_ansible_test.ansible.ping import ansible_ping_test
from briefcase_ansible_test.ansible.droplet_management import run_droplet_playbook
from briefcase_ansible_test.test_multiprocessing import test_multiprocessing
from briefcase_ansible_test.test_worker_import import test_worker_import
from briefcase_ansible_test.test_display_import import test_display_import
from briefcase_ansible_test.test_task_executor_imports import test_task_executor_imports
from briefcase_ansible_test.test_direct_import import test_direct_import
from briefcase_ansible_test.test_module_level_sim import test_module_level_sim
from briefcase_ansible_test.test_import_trace import test_import_trace
from briefcase_ansible_test.test_ansible_workerprocess import test_ansible_workerprocess
from briefcase_ansible_test.test_simple_workerprocess import test_simple_workerprocess
from briefcase_ansible_test.test_ssh_connection import test_ssh_connection as test_ssh_connection_module
from briefcase_ansible_test.test_ios_multiprocessing_integration import test_ios_multiprocessing_integration


class BriefcaseAnsibleTest(toga.App):
    def __init__(self, *args, **kwargs):
        """Construct the Toga application."""
        super().__init__(*args, **kwargs)
        # Store a set for background tasks to prevent garbage collection
        self.background_tasks = set()
        self.app_logger = None

    def startup(self):
        """Initialize the application."""
        # Set up logging first
        log_file = setup_app_logging(self.paths)
        self.app_logger = AppLogger()
        
        # Store a reference to the main event loop for background threads
        self.main_event_loop = asyncio.get_event_loop()

        # Define button configurations as tuples: (label, callback, tooltip)
        button_configs = [
            (
                "Local Ansible Ping Test",
                lambda widget: ansible_ping_test(self, widget),
                "Run Ansible ping test",
            ),
            (
                "Test SSH Connection (ed25519)",
                lambda widget: self.background_task_runner.run_task(
                    lambda: test_ssh_connection(ui_updater=self.ui_updater),
                    "Testing SSH Connection with ed25519...",
                ),
                "Test SSH connection using ed25519 key",
            ),
            (
                "Generate ED25519 Key",
                lambda widget: self.background_task_runner.run_task(
                    lambda: generate_ed25519_key(self.paths.app, self.ui_updater),
                    "Generating ED25519 key...",
                ),
                "Generate ED25519 SSH key using cryptography library",
            ),
            (
                "Test SSH Connection with Generated Key",
                lambda widget: self.background_task_runner.run_task(
                    lambda: test_ssh_connection_with_generated_key(self.paths, self.ui_updater),
                    "Testing SSH Connection with generated key...",
                ),
                "Test SSH connection using the generated ED25519 key",
            ),
            (
                "Create rtorrent Droplet",
                lambda widget: self.background_task_runner.run_task(
                    lambda: run_droplet_playbook(self.paths, self.ui_updater),
                    "Creating rtorrent droplet...",
                ),
                "Run the rtorrent droplet creation playbook from night2",
            ),
        ]

        # Create action buttons using UIComponents
        action_buttons = UIComponents.create_action_buttons(self, button_configs)

        # Create output area and status label
        self.output_view, self.status_label = UIComponents.create_output_area()

        # Create UI updater and background task runner with logger
        self.ui_updater = UIUpdater(
            self.output_view, self.status_label, self.main_event_loop, self.app_logger.logger
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
        # Run the task in a background thread with defaults
        self.background_task_runner.run_task(
            lambda: test_ssh_connection(ui_updater=self.ui_updater),
            "Testing Paramiko connection..."
        )


def main():
    return BriefcaseAnsibleTest()
