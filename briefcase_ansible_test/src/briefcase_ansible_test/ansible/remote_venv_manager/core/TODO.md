# venv_management TODO - Mobile Ansible Applications

## Mobile App Context

We are developing two distinct mobile applications with overlapping technology:

### 1. Torrent Deployment App 🌊
**Primary Goal**: Deploy DigitalOcean nodes to download torrents based on user requests
- **User Story**: User clicks magnet link → iOS app triggers → DO droplet created → torrent downloaded → files transferred → cleanup
- **Ansible Usage**: Simple, predefined playbooks for DO droplet management
- **Collection Dependencies**: Fixed (community.digitalocean, basic modules)
- **Venv Strategy**: Single persistent venv with known dependencies

### 2. Mobile Ansible Platform 🛠️
**Primary Goal**: Run and deploy Ansible playbooks from iOS with limited collection support
- **User Story**: User uploads/selects playbook → app analyzes dependencies → creates appropriate venv on target host → executes playbook
- **Ansible Usage**: Variable playbooks uploaded by users
- **Collection Dependencies**: Dynamic, requires analysis
- **Venv Strategy**: Multiple dynamic venvs based on playbook requirements

## Architecture Decisions

### Collection Analysis Integration
- **Location**: `../collection_analysis/` module (separate from venv_management)
- **iOS Compatibility**: Light dependencies make it suitable for iOS inclusion
- **Usage Trigger**: Only when user uploads new/unknown playbooks in Mobile Ansible Platform

### Venv Management Strategies

#### App 1: Torrent Deployment
```python
# Simple, fixed dependencies
TORRENT_DEPENDENCIES = {
    'collections': ['community.digitalocean'],
    'python_packages': ['ansible-core', 'requests', 'urllib3']
}

# Single venv creation at app startup
def ensure_torrent_venv():
    return run_playbook_with_venv(
        venv_name="torrent_deployment",
        collections=TORRENT_DEPENDENCIES['collections'],
        python_packages=TORRENT_DEPENDENCIES['python_packages'],
        persist=True
    )
```

#### App 2: Mobile Ansible Platform
```python
# Dynamic analysis when needed
def handle_user_playbook(playbook_content):
    # 1. Analyze playbook dependencies
    from ..analysis import analyze_collection
    deps = analyze_playbook_dependencies(playbook_content)
    
    # 2. Create/reuse appropriate venv
    venv_name = generate_venv_name_from_deps(deps)
    return run_playbook_with_venv(
        venv_name=venv_name,
        collections=deps.collections,
        python_packages=deps.python_packages,
        persist=True
    )
```

## Current Status

### Completed ✅
1. **venv_management** - Core venv creation and management
2. **collection_analysis** - Dependency detection system (moved to separate module)
3. **Module separation** - Clean boundaries between venv and analysis concerns

### Removed ❌
1. **auto_executor.py** - Over-engineered solution removed for clarity
2. **dependency_scanner.py** - Obsolete YAML-based analysis removed
3. **examples/** - Unnecessary complexity removed

## Next Steps by Application

### For Torrent Deployment App (Priority 1)
1. **Validate DO Integration** - Test `start_rtorrent_droplet.yml` with fixed venv
2. **Optimize for iOS** - Ensure reliable operation in iOS constraints
3. **Error Handling** - Robust handling of DO API failures
4. **Cost Controls** - Automatic cleanup and monitoring

### For Mobile Ansible Platform (Priority 2)
1. **Collection Analysis Integration** - Wire up dynamic dependency detection
2. **Playbook Upload UI** - Interface for users to provide playbooks
3. **Venv Profile Management** - Save/reuse venv configurations
4. **iOS Compatibility Testing** - Determine which collections work on iOS

## Development Strategy

### Phase 1: Torrent App Foundation
- Focus on single-purpose, reliable torrent deployment
- Fixed dependencies, minimal complexity
- Prove iOS + Ansible + DO integration works

### Phase 2: Mobile Ansible Expansion  
- Add dynamic playbook support
- Integrate collection analysis for dependency detection
- Build venv profile management system

## Key Design Principles

1. **Fail Fast** - No silent failures or hidden fallbacks
2. **KISS** - Simple solutions over complex abstractions  
3. **Clear User Stories** - Each feature maps to specific user needs
4. **iOS Constraints** - Design within mobile platform limitations
5. **Cost Awareness** - Always consider DO resource costs

## File Structure
```
ansible/
├── collection_analysis/         # Dependency detection (shared)
│   ├── findimports_analyzer.py
│   ├── static_dependency_analyzer.py  
│   └── analyze_collections.py
├── venv_management/             # Venv lifecycle management
│   ├── executor.py              # Core venv operations
│   ├── metadata.py             # Venv metadata tracking
│   └── ui.py                   # UI integration helpers
└── droplet_executor.py          # DO-specific operations
```

## Success Metrics

### Torrent App
- Reliable magnet link → downloaded files workflow
- Sub-$1 cost per torrent download
- <5 minute end-to-end time

### Mobile Ansible Platform  
- Support for common Ansible collections
- Automatic dependency resolution for user playbooks
- Reliable remote execution from iOS