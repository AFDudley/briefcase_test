# Coding Standards and Style Guide

## Overview

This document defines the coding standards and style guidelines for the briefcase_ansible_test refactoring project. All code must adhere to these standards before committing.

## Tools and Enforcement

### Required Tools for Every Commit

1. **Black** - Code formatter
   ```bash
   black --line-length 88 src/
   ```

2. **Flake8** - Style guide enforcement
   ```bash
   flake8 src/ --max-line-length 88 --extend-ignore E203,W503
   ```

3. **Pyright** - Type checking
   ```bash
   pyright src/
   ```

### Pre-commit Workflow

Before each commit:
```bash
# Format code
black src/

# Check style
flake8 src/

# Check types
pyright src/

# Run tests
pytest tests/
```

## PEP 8 Best Practices

### Naming Conventions

- **Functions**: `lowercase_with_underscores`
- **Classes**: `CapitalizedWords`
- **Constants**: `UPPERCASE_WITH_UNDERSCORES`
- **Private methods**: `_leading_underscore`
- **Module-private**: `_leading_underscore`

### Code Organization

```python
# Standard library imports
import os
import sys
from typing import Optional, Dict, List

# Third-party imports
import paramiko
from ansible.parsing.dataloader import DataLoader

# Local imports
from briefcase_ansible_test.utils.data_processing import parse_command_args
```

### Function Guidelines

- Maximum function length: 50 lines
- Maximum complexity (McCabe): 15
- Clear, descriptive names
- Type hints for all parameters and returns

## Functional Programming Style

### 1. Pure Functions

Prefer pure functions that:
- Return values based solely on inputs
- Have no side effects
- Are deterministic

```python
# Good - Pure function
def calculate_retry_delay(attempt: int, base_delay: float = 1.0) -> float:
    """Calculate exponential backoff delay."""
    return base_delay * (2 ** attempt)

# Bad - Side effects
def calculate_and_sleep(attempt: int) -> None:
    delay = 1.0 * (2 ** attempt)
    time.sleep(delay)  # Side effect!
```

### 2. Immutable Data Structures

Use immutable data structures where possible:

```python
from dataclasses import dataclass
from typing import FrozenSet, Tuple

@dataclass(frozen=True)
class SSHConfig:
    """Immutable SSH configuration."""
    hostname: str
    username: str
    port: int = 22

# Use tuples for fixed collections
SUPPORTED_KEY_TYPES: Tuple[str, ...] = ("ed25519", "rsa", "ecdsa")

# Use frozenset for immutable sets
ALLOWED_COMMANDS: FrozenSet[str] = frozenset({"ping", "setup", "command"})
```

### 3. Function Composition

Build complex operations from simple functions:

```python
from functools import partial
from typing import Callable

# Simple functions
def validate_path(path: str) -> bool:
    return os.path.exists(path)

def normalize_path(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))

# Compose functions
def process_path(path: str) -> Optional[str]:
    """Normalize and validate a path."""
    normalized = normalize_path(path)
    return normalized if validate_path(normalized) else None
```

### 4. Avoid Mutable State

Minimize mutable state and prefer returning new values:

```python
# Good - Return new data
def add_host_to_inventory(inventory: Dict[str, List[str]],
                         group: str,
                         host: str) -> Dict[str, List[str]]:
    """Add host to inventory group, returning new inventory."""
    new_inventory = inventory.copy()
    new_inventory[group] = inventory.get(group, []) + [host]
    return new_inventory

# Bad - Mutate in place
def add_host_to_inventory_bad(inventory: Dict[str, List[str]],
                             group: str,
                             host: str) -> None:
    """Mutates inventory in place."""
    if group not in inventory:
        inventory[group] = []
    inventory[group].append(host)
```

## Error Handling - Fail Fast

### Let Errors Propagate

The codebase follows a fail-fast philosophy. Errors should propagate to the caller rather than being hidden or worked around.

```python
# Good - Let errors propagate
def load_config_file(path: str) -> Dict[str, Any]:
    """Load JSON config file."""
    with open(path) as f:
        return json.load(f)

# Bad - Hiding errors with fallbacks
def load_config_file_bad(path: str) -> Dict[str, Any]:
    """Load config with dangerous fallback."""
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {}  # NO! This hides failures
```

### No Silent Failures

Never use fallbacks or default values when operations fail:

```python
# Good - Clear failure
def get_ssh_key(key_path: str) -> paramiko.PKey:
    """Load SSH key, failing if not found."""
    return paramiko.Ed25519Key.from_private_key_file(key_path)

# Bad - Silent fallback
def get_ssh_key_bad(key_path: str) -> Optional[paramiko.PKey]:
    """Load SSH key with fallback."""
    try:
        return paramiko.Ed25519Key.from_private_key_file(key_path)
    except:
        return None  # NO! Caller won't know why it failed
```

### Only Catch Specific Exceptions When Necessary

If you must catch exceptions, be specific and re-raise when appropriate:

```python
# Good - Specific exception handling with context
def validate_inventory_file(path: str) -> None:
    """Validate inventory file exists and is readable."""
    try:
        with open(path) as f:
            f.read(1)  # Test readability
    except FileNotFoundError:
        raise FileNotFoundError(f"Inventory file not found: {path}")
    except PermissionError:
        raise PermissionError(f"Cannot read inventory file: {path}")
    # Any other exception propagates unchanged

# Bad - Catch-all exception handling
def validate_inventory_file_bad(path: str) -> bool:
    """Validate with catch-all."""
    try:
        with open(path) as f:
            f.read(1)
        return True
    except Exception:
        return False  # NO! Lost all error context
```

### Context Managers

Use context managers for resource management:

```python
from contextlib import contextmanager
from typing import Generator

@contextmanager
def temporary_directory() -> Generator[str, None, None]:
    """Create and clean up temporary directory."""
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
```

## Type Hints

### Complete Type Annotations

All functions must have type hints:

```python
from typing import Dict, List, Optional, Union, Callable, TypeVar

T = TypeVar('T')

def process_items(
    items: List[T],
    predicate: Callable[[T], bool],
    transform: Callable[[T], T]
) -> List[T]:
    """Process items with predicate and transform."""
    return [transform(item) for item in items if predicate(item)]
```

### Use typing.Protocol for Interfaces

```python
from typing import Protocol

class UIUpdater(Protocol):
    """Protocol for UI update operations."""

    def add_text_to_output(self, text: str) -> None:
        """Add text to output display."""
        ...

    def update_status(self, status: str) -> None:
        """Update status display."""
        ...
```

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def execute_ansible_play(
    play_dict: Dict[str, Any],
    inventory_path: str,
    ui_updater: Optional[UIUpdater] = None
) -> Result:
    """Execute an Ansible play and return results.

    Args:
        play_dict: Dictionary defining the Ansible play
        inventory_path: Path to Ansible inventory file
        ui_updater: Optional UI updater for progress reporting

    Returns:
        Result object containing either Success with play results
        or Failure with error message

    Raises:
        ValueError: If play_dict is invalid

    Example:
        >>> play = {"name": "Test", "hosts": "all", "tasks": [...]}
        >>> result = execute_ansible_play(play, "/path/to/inventory")
        >>> if isinstance(result, Success):
        ...     print(f"Play succeeded: {result.value}")
    """
    pass
```

## Code Smells to Avoid

1. **Long parameter lists** - Use dataclasses or named tuples
2. **Nested if statements** - Use early returns or guard clauses
3. **Mutable default arguments** - Use None and create inside function
4. **God objects** - Split into focused classes
5. **Side effects in getters** - Keep getters pure
6. **Bare except clauses** - Always catch specific exceptions

## Example: Refactored Function

```python
# Before - Violates multiple principles
def process_data(data, config={}):
    result = []
    for item in data:
        if item['type'] == 'A':
            if 'value' in item:
                result.append(item['value'] * 2)
        elif item['type'] == 'B':
            if 'value' in item:
                result.append(item['value'] * 3)
    config['processed'] = len(result)  # Side effect!
    return result

# After - Following functional principles
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass(frozen=True)
class ProcessingResult:
    values: List[float]
    count: int

def process_data(
    data: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None
) -> ProcessingResult:
    """Process data items based on type.

    Args:
        data: List of data items with 'type' and 'value' fields
        config: Optional configuration (unused)

    Returns:
        ProcessingResult with processed values and count
    """
    processors = {
        'A': lambda x: x * 2,
        'B': lambda x: x * 3,
    }

    values = [
        processors[item['type']](item['value'])
        for item in data
        if item.get('type') in processors and 'value' in item
    ]

    return ProcessingResult(values=values, count=len(values))
```

## Commit Message Format

```
feat: Add SSH connection context manager

- Implement ssh_client_context for automatic cleanup
- Add comprehensive error handling
- Include unit tests for success and failure cases

Verified with: black, flake8, pyright
Test: All SSH connection tests passing
```

Categories: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

## AI Adherence Guidelines

### Pre-commit Checklist

Before submitting any code, verify:

- [ ] No functions exceed 50 lines
- [ ] No try/except blocks with fallbacks or default returns
- [ ] All functions have complete type hints (parameters and returns)
- [ ] No mutable default arguments (use `None` instead)
- [ ] All imports are at module level (no lazy imports)
- [ ] No bare `except:` clauses
- [ ] All classes use `@dataclass(frozen=True)` where applicable
- [ ] No side effects in functions that could be pure
- [ ] Context managers used for all resource management
- [ ] Docstrings follow Google style format

### AI Review Prompts

Ask yourself these questions before finalizing code:

1. **"Does this function have side effects?"**
   - If yes, can it be split into pure calculation + side effect?

2. **"Am I hiding any errors?"**
   - Check for `try/except` blocks that return defaults
   - Ensure all errors propagate with context

3. **"Could this be a pure function?"**
   - Functions that only calculate/transform should return values
   - No print statements, file I/O, or state mutations

4. **"Is this function doing too much?"**
   - Each function should have a single, clear purpose
   - If you need "and" to describe it, split it

5. **"Am I using the right data structure?"**
   - Prefer immutable structures (tuple, frozenset, frozen dataclass)
   - Use dataclasses for configuration objects

### Code Review Template

When reviewing refactored code, check:

```markdown
## Code Review Checklist
- **Complexity**: No function over 50 lines
- **Imports**: All at module level
- **Types**: Complete type annotations
- **Errors**: Fail fast, no silent failures
- **State**: Minimal mutable state
- **Resources**: Context managers for cleanup
- **Style**: Black formatted, Flake8 clean
- **Docs**: Google-style docstrings
```

### Common AI Pitfalls to Avoid

1. **Over-engineering**: Don't create abstractions for single-use cases
2. **Defensive programming**: Let errors propagate, don't add "safety" fallbacks
3. **Mixing concerns**: Keep I/O, business logic, and UI updates separate
4. **Forgetting immutability**: Always use `frozen=True` for config dataclasses
5. **Complex comprehensions**: If it needs multiple lines, use a regular loop
