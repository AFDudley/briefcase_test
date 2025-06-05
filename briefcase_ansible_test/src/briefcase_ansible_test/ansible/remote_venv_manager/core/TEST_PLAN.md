# Virtual Environment Management Test Plan

## Overview

This test plan covers unit, integration, and end-to-end testing for the venv_management module. The module provides functionality for creating and managing Python virtual environments on remote hosts for Ansible execution.

## Test Scope

### Components to Test
1. **metadata.py** - Pure functions for venv metadata management
2. **executor.py** - Functions for running playbooks with venvs
3. **ui.py** - Functions for formatting venv information
4. **Ansible playbooks** - YAML playbooks for venv operations
5. **Ansible role** - venv_executor role functionality

### Test Categories

#### 1. Unit Tests

##### metadata.py
- **test_generate_venv_name()**
  - Test with persistent=False (should include timestamp)
  - Test with persistent=True and custom name
  - Test with empty/None custom name
  - Verify name format and uniqueness

- **test_create_metadata_dict()**
  - Test with all required fields
  - Test with optional fields (collections, packages)
  - Test with missing required fields (should handle gracefully)
  - Verify metadata version is included

- **test_save_venv_metadata()**
  - Test successful save to correct path
  - Test directory creation if not exists
  - Test overwrite existing metadata
  - Test handling of write permissions error
  - Verify JSON format is valid

- **test_load_venv_metadata()**
  - Test loading existing metadata
  - Test loading non-existent metadata (should return None)
  - Test loading corrupted JSON (should handle gracefully)
  - Test loading outdated metadata version

- **test_list_all_venvs()**
  - Test with empty metadata directory
  - Test with multiple venv metadata files
  - Test filtering by host
  - Test handling of corrupted metadata files

- **test_delete_venv_metadata()**
  - Test successful deletion
  - Test deletion of non-existent metadata
  - Test handling of permission errors

##### executor.py
- **test_prepare_extra_vars()**
  - Test merging default vars with user vars
  - Test overriding default values
  - Test with empty user vars
  - Test venv name generation

- **test_run_venv_wrapper()**
  - Test with valid parameters
  - Test with missing required parameters
  - Test callback integration
  - Test error handling from Ansible execution

- **test_run_playbook_with_venv()**
  - Test temporary venv creation and cleanup
  - Test persistent venv creation
  - Test with collections requirement
  - Test with extra packages
  - Test error propagation
  - Test metadata creation

##### ui.py
- **test_format_venv_info()**
  - Test with complete metadata
  - Test with minimal metadata
  - Test formatting of dates, sizes, versions
  - Test truncation of long lists

- **test_format_venv_list()**
  - Test with empty list
  - Test with single venv
  - Test with multiple venvs
  - Test grouping by host
  - Test sorting order

- **test_format_venv_summary()**
  - Test with various venv states
  - Test size calculations
  - Test age calculations

#### 2. Integration Tests

##### Ansible Playbook Tests
- **test_venv_wrapper_playbook()**
  - Test complete workflow execution
  - Test parameter passing
  - Test conditional execution paths
  - Test cleanup on failure

- **test_collect_metadata_playbook()**
  - Test metadata collection accuracy
  - Test handling of missing commands
  - Test output formatting

- **test_execute_in_venv_playbook()**
  - Test playbook execution within venv
  - Test environment variable propagation
  - Test error handling

##### Ansible Role Tests
- **test_venv_executor_role()**
  - Test venv creation with different Python versions
  - Test package installation
  - Test collection installation
  - Test idempotency
  - Test cleanup functionality

#### 3. End-to-End Tests

- **test_complete_workflow()**
  - Create temporary venv
  - Install Ansible and collections
  - Execute test playbook
  - Verify results
  - Verify automatic cleanup

- **test_persistent_venv_workflow()**
  - Create persistent venv
  - Execute multiple playbooks
  - Verify venv reuse
  - Test metadata updates
  - Manual cleanup

- **test_error_scenarios()**
  - Test network failures during package installation
  - Test insufficient disk space
  - Test permission errors
  - Test invalid Python versions
  - Test corrupted venv recovery

#### 4. Performance Tests

- **test_venv_creation_time()**
  - Measure time for minimal venv
  - Measure time with collections
  - Compare temporary vs persistent

- **test_metadata_operations_performance()**
  - Test loading large metadata sets
  - Test concurrent metadata access

#### 5. Mock/Fixture Requirements

- **Mock SSH connections** for unit tests
- **Mock file system** for metadata operations
- **Mock Ansible runner** for executor tests
- **Test inventory** with multiple hosts
- **Sample playbooks** for testing
- **Pre-created metadata** files for testing

## Test Data

### Sample Metadata
```json
{
  "venv_name": "test_env_001",
  "venv_path": "/home/test/ansible-venvs/test_env_001",
  "created_at": "2024-01-15T10:30:00",
  "target_host": "test.local",
  "persistent": false,
  "python_version": "Python 3.10.6",
  "ansible_version": ["ansible [core 2.15.0]"],
  "pip_packages": ["ansible-core==2.15.0"],
  "ansible_collections": {},
  "venv_size": "150M",
  "last_updated": "2024-01-15T10:30:00",
  "metadata_version": "1.0"
}
```

### Test Hosts
- `localhost` - Local testing
- `test.local` - Mock remote host
- `invalid.host` - For error testing

## Test Execution Strategy

1. **Unit tests** run on every commit
2. **Integration tests** run on pull requests
3. **E2E tests** run before releases
4. **Performance tests** run weekly

## Success Criteria

- All unit tests pass with 90%+ code coverage
- Integration tests verify Ansible components work correctly
- E2E tests confirm real-world usage scenarios
- No performance regressions
- Error scenarios handled gracefully

## Testing Tools

- **pytest** - Test framework
- **pytest-mock** - Mocking functionality
- **pytest-cov** - Coverage reporting
- **pytest-asyncio** - Async test support
- **ansible-test** - Ansible component testing

## Notes

- Tests should be iOS-compatible where applicable
- Mock system dependencies that don't exist on iOS
- Test both success and failure paths
- Verify cleanup happens in all scenarios
- Test concurrent operations where relevant