# Tests for iOS Threading-Based Multiprocessing

This directory contains comprehensive tests for the iOS threading-based multiprocessing implementation.

## 🏗️ Test Structure

```
tests/
├── conftest.py                    # Pytest configuration
├── README.md                      # This file
├── test_*.py                      # Unit tests
├── integration/                   # Integration tests
│   ├── test_workerprocess.py     # Ansible WorkerProcess patterns
│   ├── test_ansible_with_multiprocessing.py
│   └── test_*.py                 # Component interaction tests
└── system/                       # Full system tests
    ├── test_ansible_comprehensive.py  # Complete Ansible validation
    ├── test_ansible_play_final.py     # End-to-end playbook execution
    └── test_*.py                      # Full system validation
```

## 🧪 Test Categories

### Unit Tests (`./`)
Test individual components in isolation:
- **`test_threadprocess.py`** - ThreadProcess class functionality
- **`test_queue_inheritance.py`** - Queue implementations and inheritance
- **`test_multiprocessing.py`** - General multiprocessing API compatibility

### Integration Tests (`integration/`)
Test component interactions:
- **`test_workerprocess.py`** - Ansible WorkerProcess pattern compatibility
- **`test_ansible_with_multiprocessing.py`** - Ansible + multiprocessing integration
- **`test_improved_patch.py`** - System patching functionality
- **`test_run_method_fix.py`** - Critical run() method inheritance support

### System Tests (`system/`)
Test complete end-to-end functionality:
- **`test_ansible_comprehensive.py`** - Full Ansible feature validation
- **`test_ansible_play_final.py`** - Complete playbook execution
- **`test_ansible_exact.py`** - Specific Ansible scenario testing
- **`test_ansible_fixed.py`** - Regression tests for fixed issues

## 🚀 Running Tests

### Quick Start
```bash
# From the _multiprocessing directory
python run_tests.py

# Or using pytest directly
python -m pytest tests/
```

### Selective Testing
```bash
# Unit tests only
python run_tests.py unit

# Integration tests only  
python run_tests.py integration

# System tests only
python run_tests.py system

# Verbose output
python run_tests.py --verbose
```

### Advanced Usage
```bash
# Run specific test file
python -m pytest tests/test_threadprocess.py

# Run tests matching pattern
python -m pytest tests/ -k "threadprocess"

# Run with coverage
python -m pytest tests/ --cov=briefcase_ansible_test.utils._multiprocessing

# Run only fast tests (skip slow system tests)
python -m pytest tests/ -m "not slow"
```

## 📊 Expected Results

All tests should pass with the following approximate timings:

### Unit Tests (~1-2 seconds)
- ✅ ThreadProcess basic functionality
- ✅ Queue operations and timeout handling
- ✅ Synchronization primitives

### Integration Tests (~5-10 seconds)
- ✅ WorkerProcess pattern compatibility
- ✅ Ansible component integration
- ✅ System patching validation

### System Tests (~30-60 seconds)
- ✅ Complex Ansible playbook execution
- ✅ Error handling and recovery
- ✅ Performance validation
- ✅ Sequential execution testing

## 🔧 Test Configuration

### Environment Setup
Tests automatically apply necessary patches:
- iOS system compatibility (pwd, grp, getpass)
- Multiprocessing module patching
- Ansible environment configuration

### Markers
Tests are marked for selective execution:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.system` - System tests
- `@pytest.mark.slow` - Long-running tests

### Dependencies
Tests require:
- Ansible (for integration and system tests)
- pytest (test runner)
- Standard library modules (threading, queue, etc.)

## 🚨 Troubleshooting

### Common Issues

**Import Errors**
```
ModuleNotFoundError: No module named 'briefcase_ansible_test'
```
Solution: Ensure you're running from the correct directory with proper PYTHONPATH.

**Hanging Tests**
```
Test appears to hang indefinitely
```
Solution: Check for deadlocks in threading implementation. Use timeout flags:
```bash
python -m pytest tests/ --timeout=30
```

**Ansible Import Failures**
```
ImportError: No module named 'ansible'
```
Solution: Install Ansible: `pip install ansible`

### Debug Mode
For debugging test failures:
```bash
# Run with maximum verbosity
python -m pytest tests/ -vvv --tb=long

# Run single test with debugging
python -m pytest tests/test_threadprocess.py::test_specific_function -vvv --tb=long --capture=no
```

### Performance Issues
If tests run slowly:
```bash
# Profile test execution
python -m pytest tests/ --durations=10

# Run only fast tests
python -m pytest tests/ -m "not slow"
```

## 📈 Test Coverage

Expected coverage areas:
- **Process Creation**: Both target function and run() method patterns
- **Queue Operations**: All queue types with timeout and exception handling
- **Synchronization**: All threading-based synchronization primitives
- **Error Handling**: Exception propagation and serialization
- **Ansible Integration**: Complete TaskQueueManager and WorkerProcess compatibility

## 🎯 Adding New Tests

When adding new tests:

1. **Choose the right category**:
   - Unit: Testing individual components
   - Integration: Testing component interaction
   - System: Testing complete workflows

2. **Use appropriate markers**:
   ```python
   import pytest
   
   @pytest.mark.unit
   def test_threadprocess_basic():
       pass
   
   @pytest.mark.slow
   @pytest.mark.system
   def test_complex_ansible_playbook():
       pass
   ```

3. **Follow naming conventions**:
   - Test files: `test_*.py`
   - Test functions: `test_*`
   - Test classes: `Test*`

4. **Include proper documentation**:
   ```python
   def test_feature():
       """Test that feature works correctly.
       
       This test validates that the feature handles
       edge cases and error conditions properly.
       """
   ```

This test suite ensures the iOS threading-based multiprocessing implementation is robust, reliable, and ready for production use with Ansible!