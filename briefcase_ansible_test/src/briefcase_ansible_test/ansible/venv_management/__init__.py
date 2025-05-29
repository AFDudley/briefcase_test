"""
Virtual environment management for Ansible playbooks.

This module provides functional utilities for creating, managing, and tracking
virtual environments on remote hosts for Ansible execution.
"""

from .metadata import (
    save_venv_metadata,
    load_venv_metadata,
    list_all_venvs,
    get_venv_index,
    update_venv_index,
)

from .executor import (
    run_playbook_with_venv,
    check_venv_exists,
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
    "get_venv_index",
    "update_venv_index",
    # Executor functions
    "run_playbook_with_venv",
    "check_venv_exists",
    "get_venv_path",
    "create_venv_vars",
    # UI formatting functions
    "format_venv_status",
    "format_venv_list",
    "format_metadata_summary",
]