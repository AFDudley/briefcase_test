# Source Directory Structure

This document provides an overview of the `src/` directory organization for the briefcase_ansible_test iOS application.

## Directory Overview

```
src/
├── briefcase_ansible_test.dist-info/    # Package distribution metadata
├── briefcase_ansible_test/              # Main application package
│   ├── __init__.py                     # Package initialization
│   ├── __main__.py                     # Application entry point
│   ├── app.py                          # Main Toga application class
│   ├── ui.py                           # UI components and threading helpers
│   ├── ssh_utils.py                    # SSH/Paramiko connection utilities
│   │
│   ├── ansible/                        # Ansible-specific functionality
│   │   ├── __init__.py                # Module exports
│   │   ├── inventory.py               # Inventory parsing
│   │   ├── ping.py                    # Ansible ping implementation
│   │   ├── playbook.py                # Playbook execution
│   │   ├── ios_setup.py               # iOS-specific Ansible setup
│   │   ├── callbacks.py               # Custom Ansible callbacks
│   │   ├── ansible_config.py          # Ansible configuration
│   │   └── debug_patches.py           # Debug utilities
│   │
│   ├── ansible_collections/           # Ansible collections directory
│   │   └── ansible/builtin/          # Built-in Ansible modules
│   │       └── plugins/modules/      # Module implementations
│   │           └── ping.py           # Custom ping module
│   │
│   ├── utils/                         # Utility modules
│   │   ├── __init__.py
│   │   ├── system_utils.py           # Cross-platform utilities
│   │   ├── ios_patches.py            # iOS-specific patches
│   │   ├── mocks/                    # Mock implementations for iOS
│   │   │   ├── pwd_mock.py          # Mock pwd module
│   │   │   ├── grp_mock.py          # Mock grp module
│   │   │   └── subprocess/          # Mock subprocess module
│   │   └── multiprocessing/          # Custom multiprocessing implementation
│   │       ├── __init__.py           # Auto-patching and exports
│   │       ├── process.py            # ThreadProcess implementation
│   │       ├── queues.py             # Queue implementations
│   │       ├── synchronize/          # Synchronization primitives
│   │       ├── context.py            # Context management
│   │       ├── docs/                 # Documentation
│   │       ├── tests/                # Test suite
│   │       └── dev/                  # Development utilities
│   │
│   ├── resources/                     # Application resources
│   │   ├── inventory/                # Sample inventory files
│   │   ├── playbooks/               # Sample playbooks
│   │   └── keys/                    # SSH keys for testing
│   │
│   └── test_*.py                     # Various test scripts
```

## Key Components

### 1. Main Application (`briefcase_ansible_test/`)

The main application package contains:
- **app.py**: The Toga application class that defines the UI and button handlers
- **ui.py**: UI helper classes including `BackgroundTaskRunner` for threading
- **ssh_utils.py**: Paramiko-based SSH connection testing

### 2. Ansible Integration (`ansible/`)

This directory contains all Ansible-specific functionality:
- **inventory.py**: Parse and display Ansible inventory files
- **playbook.py**: Execute Ansible playbooks via Paramiko
- **ping.py**: Run Ansible ping tests locally
- **ios_setup.py**: iOS-specific setup including temp directory configuration
- **callbacks.py**: Custom Ansible callbacks for UI updates

### 3. iOS Threading-Based Multiprocessing (`utils/multiprocessing/`)

The crown jewel of the iOS compatibility layer:

#### Core Implementation
- **__init__.py**: Auto-patches system modules on import, exports all APIs
- **process.py**: `ThreadProcess` class that replaces `multiprocessing.Process`
- **queues.py**: Thread-safe queue implementations with timeout support
- **synchronize/**: Threading-based synchronization primitives
- **context.py**: Context management for different "start methods"

#### Documentation (`docs/`)
- **README.md**: User guide and examples
- **PACKAGE_SUMMARY.md**: High-level overview and achievements
- **IMPLEMENTATION_NOTES.md**: Technical deep dive
- **TESTING_GUIDE.md**: Testing methodology
- **CHANGELOG.md**: Development history

#### Testing (`tests/`)
- Unit tests for individual components
- Integration tests for component interactions
- System tests for full Ansible integration

#### Development Tools (`dev/`)
- Debug scripts documenting the development process
- Performance benchmarking utilities

### 4. iOS Mocks (`utils/mocks/`)

Mock implementations for system modules not available on iOS:
- **pwd_mock.py**: Mock user/password database
- **grp_mock.py**: Mock group database
- **subprocess/**: Mock subprocess module for iOS compatibility

### 5. Resources (`resources/`)

Application resources including:
- Sample inventory files
- Sample playbooks
- SSH keys for testing

## Integration Flow

1. **Application Start**: 
   - `__main__.py` imports the app and starts the main loop
   - The multiprocessing module is auto-patched on import

2. **iOS Setup**:
   - System modules (pwd, grp) are mocked
   - Multiprocessing is replaced with threading implementation
   - Ansible temp directories are configured

3. **Ansible Execution**:
   - Uses the custom multiprocessing implementation
   - WorkerProcess instances run as threads
   - Queue communication works across threads
   - Full playbook execution is supported

## Key Features

- **Zero-Code Migration**: The multiprocessing module is automatically replaced
- **Full API Compatibility**: Drop-in replacement for standard multiprocessing
- **Ansible Support**: Complete compatibility with Ansible's TaskQueueManager
- **iOS Optimized**: Works within iOS sandbox restrictions
- **Production Ready**: Comprehensive testing and documentation

## Usage

The application automatically sets up the iOS compatibility layer when imported. Developers can use standard Python multiprocessing and Ansible APIs without modification.