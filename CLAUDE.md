# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python application called "briefcase_ansible_test" created using [Briefcase](https://briefcase.readthedocs.io/), a packaging tool from the [BeeWare](https://beeware.org/) project. The app is specifically designed to test running Ansible within an iOS application packaged with Briefcase.

## Architecture

- The application uses [Toga](https://toga.readthedocs.io/) as the UI framework, which provides a native user interface on iOS.
- The application includes workarounds for iOS-specific limitations:
  - Mocks for system modules missing on iOS (pwd, grp)
  - Custom implementations of getuser and executable checks for iOS compatibility
  - Paramiko patches for modern Python compatibility on iOS
- The main application structure follows Briefcase's standard layout:
  - `app.py` contains the main application class and entry point
  - `__main__.py` handles launching the application when run directly
  - `ansible.py` contains Ansible-related functionality
  - `ssh_utils.py` provides SSH connection functionality with Paramiko
  - `ui.py` contains UI components and helpers for threading
  - `utils/system_utils.py` contains iOS compatibility utilities

## Development Commands

### Setting Up

```bash
# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Running the Application

```bash
# Run the app in development mode
briefcase dev

# Run on a specific platform
briefcase dev -p macOS
briefcase dev -p iOS
briefcase dev -p android
briefcase dev -p windows
briefcase dev -p linux
briefcase dev -p web
```

### Building the Application

```bash
# Build the app for the current platform
briefcase build

# Build for a specific platform
briefcase build -p macOS
briefcase build -p iOS
briefcase build -p android
briefcase build -p windows
briefcase build -p linux
briefcase build -p web
```

### Running Tests

```bash
# Run all tests
pytest

# Run a specific test file
pytest tests/test_app.py

# Run with verbose output
pytest -v
```

### Packaging and Distribution

```bash
# Package the application for distribution
briefcase package

# Package for a specific platform
briefcase package -p macOS
```

## Platform-Specific Notes

- While Briefcase supports multiple platforms, this application focuses specifically on iOS:
  - The app demonstrates how to overcome iOS limitations and restrictions while providing Ansible functionality
  - Special configurations are made for iOS-specific dependencies in pyproject.toml
  - Contains workarounds for running SSH and Ansible operations within iOS sandbox restrictions
  - Includes mock implementations for system modules not available on iOS

## Key Features

- Parse and display Ansible inventory files
- Parse Ansible playbooks
- Test SSH connections using Paramiko with custom patches for iOS
- Run Ansible playbooks via Paramiko
- Perform Ansible ping tests against hosts
- Thread management for responsive UI on iOS