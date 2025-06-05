# Remote Venv Manager - Orchestration Implementation Plan

## Overview
This document outlines the implementation plan for the orchestration layer that will provide playbook-to-venv mapping with content-based hashing and host tracking.

## Implementation Order

### 1. Playbook Processing Pipeline
**Goal**: Create deterministic playbook → venv specification mapping

**Components**:
```python
def process_playbook(playbook_path: str) -> Tuple[str, Dict]:
    """
    Process playbook through validation, normalization, and analysis.
    
    Pipeline:
    1. Run ansible-lint for validation
    2. Run ansible-format for normalization  
    3. Generate SHA256 hash of normalized content
    4. Run collection analysis for dependencies
    
    Returns:
        Tuple of (venv_spec_name, venv_specification)
    """
```

**Files to Create**:
- `playbook_processor.py` - Main processing pipeline
- `content_hasher.py` - Deterministic content hashing
- Integration with `../analysis/` for dependency detection

### 2. Venv Specification File Format
**Goal**: Standardized venv specification storage

**File Format**:
```yaml
# venv_specs/start_rtorrent_droplet_a1b2c3d4.yml
name: start_rtorrent_droplet_a1b2c3d4
source_playbook: start_rtorrent_droplet.yml
content_hash: a1b2c3d4
collections:
  - community.digitalocean
python_packages:
  - ansible-core
  - requests
  - urllib3
created: "2024-01-15T10:30:00"
```

**Files to Create**:
- `venv_specification.py` - Spec file management
- `spec_storage.py` - File I/O operations

### 3. Host Tracking System
**Goal**: Track which venvs are installed on which hosts

**File Format**:
```yaml
# host_venvs/night2.lan.yml
hostname: night2.lan
installed_venvs:
  - name: start_rtorrent_droplet_a1b2c3d4
    path: /home/ansible/venvs/start_rtorrent_droplet_a1b2c3d4
    installed_date: "2024-01-15T10:35:00"
```

**Files to Create**:
- `host_tracker.py` - Host venv state management
- `venv_registry.py` - Cross-host venv lookup

### 4. Inventory File Management
**Goal**: Sync venv state with Ansible inventory

**Inventory Integration**:
```ini
# inventory/hosts
[jump_hosts]
night2.lan ansible_user=rix installed_venvs='["start_rtorrent_droplet_a1b2c3d4"]'
```

**Functions to Create**:
```python
def update_inventory_venvs(hostname: str, venv_list: List[str]) -> None:
    """Update installed_venvs variable in inventory file"""

def get_inventory_venvs(hostname: str) -> List[str]:
    """Read installed_venvs from inventory file"""

def sync_inventory_with_host_files() -> None:
    """Ensure inventory matches host_venvs/ files"""
```

**Files to Create**:
- `inventory_manager.py` - Inventory file manipulation
- `inventory_sync.py` - Keep inventory and host files consistent

### 5. Integration with Existing Venv Management
**Goal**: Wire orchestration into existing `../core/` functionality

**Integration Points**:
```python
def deploy_playbook_with_orchestration(
    playbook_path: str,
    target_host: str,
    force_recreate: bool = False
) -> VenvExecutionResult:
    """
    High-level playbook deployment with automatic venv management.
    
    Flow:
    1. Process playbook → get venv spec
    2. Check if venv exists on target host
    3. Create venv if needed, update tracking
    4. Execute playbook using existing core.run_playbook_with_venv()
    """
```

**Files to Create**:
- `deployment_orchestrator.py` - Main orchestration logic
- `venv_resolver.py` - Determine venv needs for playbooks

### 6. CLI Tools for Management
**Goal**: Command-line interface for orchestration features

**Commands to Add**:
```bash
# Analyze playbook and show venv spec
ansible-venv analyze playbook.yml

# Deploy playbook with auto venv management  
ansible-venv deploy playbook.yml target_host

# List venvs on host
ansible-venv list-host target_host

# Show venv specification
ansible-venv show-spec venv_name

# Clean up unused venvs
ansible-venv cleanup target_host
```

**Files to Create**:
- `cli.py` - Command-line interface
- `commands/` - Individual command implementations

## File Structure
```
orchestration/
├── __init__.py
├── IMPLEMENTATION_PLAN.md          # This file
├── playbook_processor.py           # Pipeline: lint → format → hash → analyze
├── content_hasher.py               # Deterministic content hashing
├── venv_specification.py           # Spec file format and validation
├── spec_storage.py                 # Spec file I/O operations
├── host_tracker.py                 # Host venv state management
├── venv_registry.py                # Cross-host venv lookup
├── inventory_manager.py            # Inventory file manipulation
├── inventory_sync.py               # Inventory ↔ host files sync
├── deployment_orchestrator.py     # Main orchestration logic
├── venv_resolver.py                # Playbook → venv resolution
├── cli.py                          # Command-line interface
└── commands/                       # CLI command implementations
    ├── analyze.py
    ├── deploy.py
    ├── list_host.py
    ├── show_spec.py
    └── cleanup.py
```

## Key Design Principles

### Content-Based Hashing
- Same playbook content = same venv spec = same hash
- Changes to playbook = new hash = new venv
- Deterministic through lint → format → hash pipeline

### Host State Management
- `host_venvs/` files are source of truth for each host
- Inventory `installed_venvs` synced from host files
- Supports multiple hosts with different venv sets

### Integration Strategy
- Build on existing `../core/` venv deployment
- Enhance with high-level orchestration
- Maintain backward compatibility

### Error Handling
- Fail fast with clear error messages
- No silent fallbacks or hidden behavior  
- Validate all inputs (playbooks, hosts, specs)

## Usage Examples

### App 1: Torrent Deployment (Fixed Dependencies)
```python
# Simple case - known dependencies
ensure_torrent_venv("night2.lan")  # Creates standard venv
```

### App 2: Mobile Ansible Platform (Dynamic Dependencies)
```python
# Complex case - analyze user playbook
deploy_playbook_with_orchestration(
    playbook_path="user_uploaded.yml",
    target_host="night2.lan"
)
# Auto-detects deps, creates/reuses venv, executes
```

## Success Metrics
- Deterministic venv specs (same playbook = same hash)
- No duplicate venvs for identical playbooks
- Reliable host state tracking
- Seamless integration with existing core functionality
- Clean CLI for management operations

## Dependencies
- Requires `ansible-lint` and `ansible-format` tools
- Uses existing `../analysis/` for dependency detection
- Built on existing `../core/` venv management
- Integrates with Ansible inventory files