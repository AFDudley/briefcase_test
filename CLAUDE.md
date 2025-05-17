# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a cross-platform Python application called "briefcase_ansible_test" created using [Briefcase](https://briefcase.readthedocs.io/), a packaging tool from the [BeeWare](https://beeware.org/) project. The app is intended to test running Ansible within a Briefcase application.

## Architecture

- The application uses [Toga](https://toga.readthedocs.io/) as the UI framework, which provides a platform-native user interface on various platforms.
- The main application structure follows Briefcase's standard layout:
  - `app.py` contains the main application class and entry point
  - `__main__.py` handles launching the application when run directly

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

- The application is configured for multiple platforms:
  - macOS (using Toga-Cocoa)
  - Linux (using Toga-GTK)
  - Windows (using Toga-WinForms)
  - iOS (using Toga-iOS)
  - Android (using Toga-Android)
  - Web (using Toga-Web)
- Each platform has specific dependencies defined in pyproject.toml