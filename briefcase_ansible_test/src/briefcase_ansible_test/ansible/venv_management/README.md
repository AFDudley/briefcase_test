# Virtual Environment Management for Ansible

This module provides a functional approach to managing virtual environments on remote hosts for Ansible execution.

## Overview

The venv management system allows the iOS app to:
- Create temporary or persistent Python virtual environments on target hosts
- Install Ansible and required collections in isolated environments
- Execute playbooks within these environments
- Track metadata about created environments
- Clean up temporary environments automatically

## Architecture

### Python Modules (Functional Style)

- **metadata.py** - Pure functions for managing venv metadata
- **executor.py** - Functions for running playbooks with venvs
- **ui.py** - Functions for formatting venv information for display

### Ansible Components

- **playbooks/** - Wrapper playbooks for venv management
  - `venv_wrapper.yml` - Main orchestration playbook
  - `collect_metadata.yml` - Metadata collection tasks
  - `execute_in_venv.yml` - Playbook execution within venv

- **roles/venv_executor/** - Ansible role for venv setup
  - Handles venv creation
  - Package installation
  - Collection installation

## Usage

### From Python Code

```python
from briefcase_ansible_test.ansible.venv_management import run_playbook_with_venv

# Run with temporary venv
success = run_playbook_with_venv(
    app=app,
    playbook_path="/path/to/playbook.yml",
    target_host="night2.lan",
    collections=["community.digitalocean"],
    extra_vars={"api_token": "..."}
)

# Run with persistent venv
success = run_playbook_with_venv(
    app=app,
    playbook_path="/path/to/playbook.yml",
    target_host="night2.lan",
    persist=True,
    venv_name="my_persistent_env",
    collections=["community.digitalocean"]
)
```

### Metadata Management

```python
from briefcase_ansible_test.ansible.venv_management import (
    list_all_venvs,
    load_venv_metadata,
    format_venv_list
)

# List all known venvs
venvs = list_all_venvs(app.paths)

# Get specific venv metadata
metadata = load_venv_metadata(app.paths, "my_env", "night2.lan")

# Format for UI display
display_text = format_venv_list(venvs)
```

## Metadata Storage

Metadata is stored in JSON files under `resources/venv_metadata/`:

```json
{
  "venv_name": "digitalocean_env",
  "venv_path": "/home/user/ansible-venvs/digitalocean_env",
  "created_at": "2024-01-15T10:30:00",
  "target_host": "night2.lan",
  "persistent": true,
  "python_version": "Python 3.10.6",
  "ansible_version": ["ansible [core 2.15.0]", "..."],
  "pip_packages": ["ansible-core==2.15.0", "..."],
  "ansible_collections": {"community.digitalocean": "1.24.0"},
  "venv_size": "156M",
  "last_updated": "2024-01-15T10:35:00",
  "metadata_version": "1.0"
}
```

## Benefits

1. **Isolation** - Each playbook runs in its own environment
2. **No System Changes** - No permanent modifications to target hosts
3. **Version Control** - Different Ansible versions per playbook
4. **Tracking** - Full visibility into what's installed where
5. **Efficiency** - Persistent venvs can be reused