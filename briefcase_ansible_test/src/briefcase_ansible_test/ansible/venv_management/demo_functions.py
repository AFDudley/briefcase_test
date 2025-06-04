"""
Test functions for venv management functionality.

Following functional programming principles with fail-fast error handling.
"""

import os
from datetime import datetime

from briefcase_ansible_test.ansible.venv_management import (
    run_playbook_with_venv,
    list_all_venvs,
    format_venv_list,
)

# Configuration constants
DEFAULT_HOST = "night2.lan"
DEFAULT_KEY = "briefcase_test_key"
VENV_BASE_PATH = "~/ansible-venvs"


def test_temp_venv_playbook(app, widget):
    """Run playbook in temporary venv - fail fast approach."""

    def run():
        hello_world_path = os.path.join(
            app.paths.app, "resources", "playbooks", "hello_world.yml"
        )

        # Direct call, let exceptions propagate
        run_playbook_with_venv(
            app=app,
            playbook_path=hello_world_path,
            target_host=DEFAULT_HOST,
            persist=False,
            ui_updater=app.ui_updater,
        )
        app.ui_updater.update_status("Temp venv playbook complete")

    app.background_task_runner.run_task(run, "Running playbook in temp venv...")


def test_create_venv(app, widget):
    """Create named venv with timestamp."""

    def run():
        venv_name = f"test_venv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create venv only (no playbook)
        run_playbook_with_venv(
            app=app,
            playbook_path="",  # Empty string for venv-only creation
            target_host=DEFAULT_HOST,
            persist=True,
            venv_name=venv_name,
            ui_updater=app.ui_updater,
        )
        app.ui_updater.add_text_to_output(f"\n✅ Created venv: {venv_name}\n")
        app.ui_updater.update_status("Venv created")

    app.background_task_runner.run_task(run, "Creating persistent venv...")


def test_list_venvs(app, widget):
    """List all venvs - pure function approach."""

    def run():
        # Pure function: paths → venv list → formatted string
        venvs = list_all_venvs(app.paths)
        formatted = format_venv_list(venvs)
        app.ui_updater.add_text_to_output(formatted)
        app.ui_updater.update_status("Venv list complete")

    app.background_task_runner.run_task(run, "Listing venvs...")


def test_delete_venv(app, widget):
    """Delete venv - placeholder for future implementation."""

    def run():
        # For now, just list venvs and inform about manual deletion
        venvs = list_all_venvs(app.paths)
        test_venvs = [v for v in venvs if v["name"].startswith("test_venv_")]

        if not test_venvs:
            app.ui_updater.add_text_to_output("No test venvs found.\n")
            return

        # Show oldest test venv
        oldest = sorted(test_venvs, key=lambda x: x["created"])[0]
        venv_name = oldest["name"]
        venv_path = oldest.get("venv_path", "unknown")

        app.ui_updater.add_text_to_output(
            f"Oldest test venv: {venv_name}\n"
            f"Path: {venv_path}\n"
            f"Note: Manual deletion required on host {DEFAULT_HOST}\n"
        )
        app.ui_updater.update_status("Delete info shown")

    app.background_task_runner.run_task(run, "Showing venv info...")
