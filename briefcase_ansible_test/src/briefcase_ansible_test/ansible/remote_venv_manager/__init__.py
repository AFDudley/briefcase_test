"""
Remote Venv Manager

Unified module for managing Ansible virtual environments on remote hosts.

Components:
- core: Low-level venv deployment and execution (formerly venv_management)
- analysis: Collection dependency analysis (formerly collection_analysis)
- orchestration: High-level orchestration and coordination

Main Entry Points:
- For low-level venv deployment: use core.run_playbook_with_venv()
- For collection analysis: use analysis.analyze_collection()
- For high-level orchestration: use orchestration functions (coming soon)
"""

# Expose key functionality at module level
from briefcase_ansible_test.ansible.remote_venv_manager.core import (
    run_playbook_with_venv,
)

# Analysis module imports will be available when analysis module is added

__all__ = [
    "run_playbook_with_venv",
]
