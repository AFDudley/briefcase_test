"""
Virtual environment management for Ansible playbooks.

This module provides functional utilities for creating, managing, and tracking
virtual environments on remote hosts for Ansible execution.
"""

from .metadata import (
    save_venv_metadata,
    load_venv_metadata,
    list_all_venvs,
    delete_venv_metadata,
)

from .executor import (
    run_playbook_with_venv,
    get_venv_path,
    create_venv_vars,
)

from .ui import (
    format_venv_status,
    format_venv_list,
    format_metadata_summary,
)

__all__ = [
    # Metadata functions
    "save_venv_metadata",
    "load_venv_metadata",
    "list_all_venvs",
    "delete_venv_metadata",
    # Executor functions
    "run_playbook_with_venv",
    "get_venv_path",
    "create_venv_vars",
    # UI formatting functions
    "format_venv_status",
    "format_venv_list",
    "format_metadata_summary",
]