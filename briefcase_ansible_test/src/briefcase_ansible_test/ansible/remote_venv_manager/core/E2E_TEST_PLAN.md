# End-to-End Test Plan for Virtual Environment Management

## Overview

This test plan focuses on end-to-end testing of the venv_management module using existing project resources. Tests will verify the complete workflow of creating virtual environments on remote hosts and executing Ansible playbooks within them.

## Test Resources

### Existing Assets
- **Inventory**: `resources/inventory/sample_inventory.ini`
  - night2.lan - remote host for testing
- **SSH Keys**: `resources/keys/briefcase_test_key` (with .pub)
- **Playbooks**:
  - `hello_world.yml` - Remote host test (night2)
  - `sample_playbook.yml` - Remote host test (night2)
  - `start_rtorrent_droplet.yml` - Complex DO integration test

## E2E Test Scenarios

### 1. Remote Host Tests (night2.lan)

#### Test 1.1: Remote Venv with SSH Key
```python
def test_remote_venv_with_ssh():
    """Test venv creation on remote host using SSH key"""
    # Prerequisites:
    # - night2.lan is accessible
    # - briefcase_test_key is authorized on night2.lan

    # Steps:
    # 1. Configure SSH connection with briefcase_test_key
    # 2. Create temporary venv on night2.lan
    # 3. Execute hello_world.yml
    # 4. Verify ping success
    # 5. Verify system info gathered
    # 6. Verify cleanup on night2.lan
```

#### Test 1.2: Multiple Playbook Execution
```python
def test_sequential_playbook_execution():
    """Test running multiple playbooks in same venv"""
    # Steps:
    # 1. Create persistent venv on night2.lan
    # 2. Run hello_world.yml
    # 3. Run sample_playbook.yml
    # 4. Verify both execute successfully
    # 5. Verify venv metadata updated
```

### 2. Collection Installation Tests

#### Test 2.1: Digital Ocean Collection
```python
def test_do_collection_installation():
    """Test installing collections for DO playbook"""
    # Steps:
    # 1. Create venv with community.digitalocean
    # 2. Verify collection installed
    # 3. Dry-run start_rtorrent_droplet.yml
    # 4. Verify no import errors
```

### 3. Error Handling Tests

#### Test 3.2: SSH Connection Failure
```python
def test_ssh_connection_failure():
    """Test handling of SSH connection failures"""
    # Steps:
    # 1. Use invalid SSH key
    # 2. Attempt venv creation
    # 3. Verify appropriate error message
    # 4. Verify no orphaned resources
```

### 4. Metadata Management Tests

#### Test 4.1: Metadata Lifecycle
```python
def test_metadata_lifecycle():
    """Test complete metadata management flow"""
    # Steps:
    # 1. Create multiple venvs on different hosts
    # 2. List all venvs
    # 3. Load specific venv metadata
    # 4. Update venv (add collection)
    # 5. Verify metadata updated
    # 6. Delete venv and verify metadata removed
```

### 5. UI Integration Tests

#### Test 5.1: Progress Callback
```python
def test_ui_progress_callback():
    """Test UI callback integration during venv operations"""
    # Steps:
    # 1. Create mock UI callback
    # 2. Execute venv creation with callback
    # 3. Verify callback receives:
    #    - "Creating virtual environment..."
    #    - "Installing ansible-core..."
    #    - "Running playbook..."
    #    - Progress updates
    # 4. Verify callback thread safety
```

## Test Implementation Structure

```
tests/
├── e2e/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_local_venv.py   # Local host tests
│   ├── test_remote_venv.py  # Remote host tests
│   ├── test_collections.py  # Collection tests
│   ├── test_error_handling.py
│   └── test_metadata.py
├── fixtures/
│   ├── test_playbooks/      # Additional test playbooks
│   └── mock_hosts/          # Mock host configurations
└── utils/
    ├── ssh_helpers.py       # SSH test utilities
    └── venv_helpers.py      # Venv inspection utilities
```

## Test Execution

### Prerequisites
1. Access to night2.lan (or configure alternative test host)
2. SSH key authorization configured
3. Python 3.8+ on test hosts
4. Sufficient disk space for venvs

### Running Tests

```bash
# Run all E2E tests
pytest tests/e2e/ -v

# Run specific test category
pytest tests/e2e/test_local_venv.py -v

# Run with specific host
pytest tests/e2e/ -v --test-host=myhost.local

# Skip remote tests (CI environments)
pytest tests/e2e/ -v -m "not requires_remote"
```

## Success Criteria

1. **Functionality**: All core features work as documented
2. **Reliability**: Tests pass consistently across runs
3. **Performance**: Venv creation < 60s, playbook execution < 30s
4. **Cleanup**: No orphaned venvs or metadata after tests
5. **Error Handling**: All failure modes handled gracefully

## CI/CD Integration


### Manual Testing
- Run full test suite including remote tests
- Verify against real night2.lan host
- Test with actual Digital Ocean API token

## Notes

- Tests should work within Briefcase dev environment
- Mock external dependencies where possible
- Use existing project SSH keys and inventory
- Ensure tests are idempotent
- Clean up all test artifacts
