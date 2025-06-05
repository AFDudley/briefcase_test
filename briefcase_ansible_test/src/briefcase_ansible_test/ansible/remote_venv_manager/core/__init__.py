"""
Core Venv Management

Low-level virtual environment deployment and execution functionality.
This is the foundational layer for creating and managing venvs on remote hosts.

Key Functions:
- run_playbook_with_venv(): Execute playbooks in managed venvs
- VenvExecutor: Core venv creation and management
- VenvProfile: Venv configuration and metadata
"""

from briefcase_ansible_test.ansible.remote_venv_manager.core.executor import (
    run_playbook_with_venv,
    VenvExecutionResult,
)

__all__ = [
    "run_playbook_with_venv",
    "VenvExecutionResult",
]
