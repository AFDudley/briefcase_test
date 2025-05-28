# Extraction Guide for iOS Multiprocessing Module

This guide provides instructions for extracting the iOS-compatible multiprocessing module into its own standalone repository.

## Overview

This multiprocessing implementation is a complete threading-based replacement for Python's standard multiprocessing module, designed specifically for iOS and other platforms that lack proper process support. It has been successfully tested with Ansible and provides 100% API compatibility.

## Current State

The module currently lives at:
```
src/briefcase_ansible_test/utils/multiprocessing/
```

## Target Repository Structure

Create a new repository called `ios-multiprocessing` with this structure:

```
ios-multiprocessing/
├── README.md                    # User-facing documentation
├── LICENSE                      # Choose MIT or Apache 2.0
├── pyproject.toml              # Modern Python packaging
├── setup.py                    # For pip install compatibility
├── .gitignore
├── src/
│   └── ios_multiprocessing/    # Note: renamed from just "multiprocessing"
│       ├── __init__.py         # Main module with auto-patching
│       ├── process.py          # ThreadProcess implementation
│       ├── queues.py           # Queue implementations
│       ├── context.py          # Context management
│       └── synchronize/        # Synchronization primitives
│           ├── __init__.py
│           ├── barriers.py
│           ├── conditions.py
│           ├── events.py
│           ├── locks.py
│           └── semaphores.py
├── tests/                      # Reorganized test suite
│   ├── __init__.py
│   ├── conftest.py            # Pytest configuration
│   ├── test_process.py        # From test_threadprocess.py
│   ├── test_queues.py         # From test_queue_inheritance.py
│   ├── test_multiprocessing.py # Basic functionality tests
│   └── integration/
│       ├── __init__.py
│       ├── test_ansible_compatibility.py  # From test_ansible_*.py files
│       └── test_worker_patterns.py        # From test_workerprocess.py
├── docs/                       # Cleaned up documentation
│   ├── index.md               # Main documentation
│   ├── architecture.md        # From ARCHITECTURE.md
│   ├── implementation.md      # From IMPLEMENTATION_NOTES.md
│   ├── ios-limitations.md     # From analysis docs
│   └── api-reference.md       # Generated from docstrings
├── examples/                   # New - example usage
│   ├── basic_usage.py
│   ├── worker_pattern.py
│   └── ansible_integration.py
└── benchmarks/                # From dev/benchmarks/
    ├── __init__.py
    └── performance_test.py
```

## Extraction Steps

### 1. Prepare the New Repository

```bash
# Create and initialize new repo
mkdir ~/ios-multiprocessing
cd ~/ios-multiprocessing
git init

# Create directory structure
mkdir -p src/ios_multiprocessing/synchronize
mkdir -p tests/integration
mkdir -p docs
mkdir -p examples
mkdir -p benchmarks
```

### 2. Copy Core Module Files

```bash
# From briefcase_ansible_test/src/briefcase_ansible_test/utils/multiprocessing/

# Copy main module files
cp __init__.py ~/ios-multiprocessing/src/ios_multiprocessing/
cp process.py ~/ios-multiprocessing/src/ios_multiprocessing/
cp queues.py ~/ios-multiprocessing/src/ios_multiprocessing/
cp context.py ~/ios-multiprocessing/src/ios_multiprocessing/

# Copy synchronize submodule
cp -r synchronize/* ~/ios-multiprocessing/src/ios_multiprocessing/synchronize/

# Copy tests (excluding system-specific ones)
cp tests/test_multiprocessing.py ~/ios-multiprocessing/tests/
cp tests/test_threadprocess.py ~/ios-multiprocessing/tests/test_process.py
cp tests/test_queue_inheritance.py ~/ios-multiprocessing/tests/test_queues.py
cp tests/conftest.py ~/ios-multiprocessing/tests/

# Copy documentation
cp README.md ~/ios-multiprocessing/README.md
cp ARCHITECTURE.md ~/ios-multiprocessing/docs/architecture.md
cp IMPLEMENTATION_NOTES.md ~/ios-multiprocessing/docs/implementation.md
cp IMPLEMENTATION_SUMMARY.md ~/ios-multiprocessing/docs/

# Copy benchmarks
cp -r dev/benchmarks/* ~/ios-multiprocessing/benchmarks/
```

### 3. Update Module Namespace

In the new repository, update all imports from:
```python
from briefcase_ansible_test.utils.multiprocessing import X
```

To:
```python
from ios_multiprocessing import X
```

### 4. Create Package Files

**pyproject.toml:**
```toml
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ios-multiprocessing"
version = "1.0.0"
description = "Threading-based multiprocessing implementation for iOS and platforms without process support"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: iOS",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

[project.urls]
Homepage = "https://github.com/yourusername/ios-multiprocessing"
Documentation = "https://github.com/yourusername/ios-multiprocessing/blob/main/docs/index.md"
Repository = "https://github.com/yourusername/ios-multiprocessing"
Issues = "https://github.com/yourusername/ios-multiprocessing/issues"
```

**setup.py:**
```python
from setuptools import setup, find_packages

setup(
    name="ios-multiprocessing",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
)
```

### 5. Update __init__.py

Modify the main `__init__.py` to:
1. Remove briefcase-specific imports
2. Keep the auto-patching optional
3. Update the module docstring

Key changes:
```python
# Add at the top
"""
iOS-compatible multiprocessing module using threading primitives.

This module provides a drop-in replacement for Python's multiprocessing module
on platforms where multiprocessing is not available (like iOS).

Usage:
    # Option 1: Direct import
    import ios_multiprocessing as multiprocessing
    
    # Option 2: Auto-patch system modules
    import ios_multiprocessing
    ios_multiprocessing.patch_system_modules()
    import multiprocessing  # Now uses ios_multiprocessing
"""

# Make auto-patching optional
def patch_system_modules():
    """
    Patch system modules to use our threading-based multiprocessing.
    Call this before importing any modules that use multiprocessing.
    """
    _patch_system_modules()

# Don't auto-patch on import
# _patch_system_modules()  # Comment out or remove
```

### 6. Clean Up Dependencies

Remove imports of briefcase-specific modules:
- Remove imports from `briefcase_ansible_test.utils`
- Remove iOS patches that belong to the main app
- Keep the module self-contained

### 7. Create Examples

**examples/basic_usage.py:**
```python
"""Basic usage example of ios-multiprocessing."""

import ios_multiprocessing as mp

def worker(name, queue):
    """Simple worker function."""
    result = f"Hello from {name}!"
    queue.put(result)

if __name__ == "__main__":
    # Create a queue for communication
    q = mp.Queue()
    
    # Create and start processes
    processes = []
    for i in range(3):
        p = mp.Process(target=worker, args=(f"Worker-{i}", q))
        p.start()
        processes.append(p)
    
    # Collect results
    results = []
    for _ in processes:
        results.append(q.get())
    
    # Wait for processes to complete
    for p in processes:
        p.join()
    
    print("Results:", results)
```

### 8. Update Documentation

Create a proper README.md that:
1. Explains what this is and why it exists
2. Shows installation instructions
3. Provides usage examples
4. Lists API compatibility
5. Documents iOS-specific limitations

### 9. Integration Back to Briefcase App

Update the Briefcase app to use the external module:

**In pyproject.toml:**
```toml
requires = [
    # For development
    "ios-multiprocessing @ file:///Users/yourusername/ios-multiprocessing",
    # Or from git
    # "ios-multiprocessing @ git+https://github.com/yourusername/ios-multiprocessing.git",
    # Or from PyPI (after publishing)
    # "ios-multiprocessing>=1.0.0",
]
```

**Update imports throughout the app:**
```python
# In utils/__init__.py or wherever needed
from ios_multiprocessing import patch_system_modules
patch_system_modules()
```

## Files to Exclude

Do not copy these directories/files to the new repo:
- `dev/debug/` - These are specific to Ansible debugging
- Test files that are too specific to the Briefcase app
- `pyproject.toml` and `pytest.ini` from the multiprocessing dir
- Any __pycache__ directories

## Post-Extraction Cleanup

After extracting to the new repository:
1. Remove the entire `utils/multiprocessing/` directory from the Briefcase app
2. Update all imports in the Briefcase app
3. Test that everything still works
4. Consider publishing to PyPI for easier installation

## Testing the Extraction

1. Install the new module in development mode:
   ```bash
   cd ~/ios-multiprocessing
   pip install -e .
   ```

2. Test basic functionality:
   ```bash
   python examples/basic_usage.py
   ```

3. Test with the Briefcase app:
   ```bash
   cd ~/briefcase_ansible_test
   briefcase dev
   ```

## Future Enhancements

Consider adding:
1. CI/CD with GitHub Actions
2. Code coverage reporting
3. Type hints and mypy checking
4. Sphinx documentation
5. PyPI package publishing
6. Version compatibility matrix