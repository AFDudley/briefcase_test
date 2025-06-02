# 05: Virtual Environment Management Integration

## Overview

Integration of venv_management module into app.py following functional programming principles, KISS, DRY, and fail-fast error handling.

## Core Principles

### Functional Approach
- Pure functions for all venv operations
- No hidden state or side effects in test functions
- Composable operations that can be chained
- Immutable data structures for configuration

### Fail-Fast Error Handling
- No try/except blocks that hide errors
- Let exceptions propagate to UI layer
- No fallback values - operations either succeed or fail
- Clear error messages at point of failure

### KISS Implementation
- Each test does one thing well
- No complex UI flows or nested menus
- Direct mapping: menu item → function → result
- Minimal configuration options

## Test Menu Structure

### Tests to Remove
- Start Rtorrent Droplet
- Test SSH Connection
- Droplet Management

### Simplified Test Functions

1. **Parse Inventory** (keep)
2. **Parse Playbook** (keep)
3. **Run Ansible Ping** (keep)
4. **Run Playbook via Paramiko** (keep)

5. **Run Playbook in Temp Venv**
   ```python
   def test_temp_venv_playbook(app):
       # Single function call, no error hiding
       success = run_playbook_with_venv(
           app=app,
           playbook_path=HELLO_WORLD_PATH,
           target_host="night2.lan",
           persist=False
       )
       # Let any exceptions propagate
   ```

6. **Create Named Venv**
   ```python
   def test_create_venv(app):
       venv_name = simple_prompt("Venv name: ")
       # Direct call, fail if error
       run_playbook_with_venv(
           app=app,
           playbook_path=None,  # Create only
           target_host="night2.lan",
           persist=True,
           venv_name=venv_name
       )
   ```

7. **List Venvs**
   ```python
   def test_list_venvs(app):
       # Pure function: paths → venv list → formatted string
       venvs = list_all_venvs(app.paths)
       return format_venv_list(venvs)
   ```

8. **Delete Venv**
   ```python
   def test_delete_venv(app):
       venv_name = simple_prompt("Venv to delete: ")
       # Direct deletion, no fallbacks
       delete_venv_metadata(app.paths, venv_name, "night2.lan")
   ```

## Implementation Details

### DRY Import Structure
```python
# Single import location for venv functions
from briefcase_ansible_test.ansible.venv_management import (
    run_playbook_with_venv,
    list_all_venvs,
    delete_venv_metadata,
    format_venv_list
)
```

### Functional Test Patterns

Each test follows the same pattern:
1. Get input (if needed)
2. Call pure function
3. Return result or let exception propagate

```python
def create_test_function(operation, *args):
    """Factory for creating test functions"""
    def test_func(app):
        return operation(app, *args)
    return test_func
```

### No Error Hiding

```python
# BAD - hides errors
try:
    result = run_playbook_with_venv(...)
except Exception:
    return "Operation failed"  # NO!

# GOOD - fail fast
result = run_playbook_with_venv(...)  # Let it fail
```

### Configuration Constants
```python
# Single source of truth
DEFAULT_HOST = "night2.lan"
DEFAULT_KEY = "briefcase_test_key"
VENV_BASE_PATH = "~/ansible-venvs"
```

## Benefits of This Approach

1. **Simplicity** - Each function does one thing
2. **Testability** - Pure functions are easy to test
3. **Debuggability** - Errors surface immediately
4. **Maintainability** - No hidden complexity
5. **Composability** - Functions can be combined

## Migration Checklist

- [ ] Remove complex test functions
- [ ] Add simple venv test functions
- [ ] Remove all try/except blocks that hide errors
- [ ] Ensure all functions are pure where possible
- [ ] Test fail-fast behavior
- [ ] Verify no duplicate code

## What We're NOT Doing

- No complex error recovery
- No fallback behaviors
- No nested menus or wizards
- No stateful operations
- No hidden side effects
- No lazy imports