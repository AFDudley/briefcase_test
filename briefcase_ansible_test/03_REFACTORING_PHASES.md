# Refactoring Phases - Detailed Breakdown

## Success Verification for Each Phase

### Verification Checklist
Before marking any phase complete, verify:
- [ ] App launches without errors
- [ ] Target button produces output in text area
- [ ] No new exceptions in log files at `app/logs/`
- [ ] Output text matches expected patterns (✓ for success, ✗ for errors)
- [ ] Performance is same or better (check log timestamps)
- [ ] All tests from 04_TESTING_STRATEGY.md pass

### Quick Test Commands
```bash
# Check for errors in latest log
tail -100 ~/Library/Developer/CoreSimulator/Devices/*/data/Containers/Data/Application/*/app/logs/briefcase_ansible_test_*.log | grep -i error

# Verify successful operations
grep "✅" [latest_log_file] | wc -l
```

## Phase 1: Foundation - Reusable Utilities

### 1.1 SSH Key Loading Consolidation
**File:** `ssh_utils.py`
**Work:**
- Extract common SSH key loading logic into `load_ssh_key()` function
- Support only Ed25519 to start
- Consistent error handling and UI feedback
- Update `test_ssh_connection()` and `generate_ed25519_key()` to use it

**Test:** "Test SSH Connection" button should load keys correctly

### 1.2 Path Validation Utility
**File:** `utils/system_utils.py`
**Work:**
- Add `validate_and_resolve_path()` function
- Add `find_app_resource()` function for resource location
- Update all file loading operations to use these utilities

**Test:** "Local Ansible Ping Test" should find all required files

### 1.3 Status Reporter Class
**File:** `ui/components.py`
**Work:**
```python
class StatusReporter:
    - success(message)
    - error(message)
    - warning(message)
    - get_summary()
```
- Pilot implementation in `generate_ed25519_key()`

**Test:** "Generate ED25519 Key" should show formatted status messages

## Phase 2: Context Managers

### 2.1 SSH Client Context Manager
**File:** `ssh_utils.py`
**Work:**
- Add `ssh_client_context()` context manager
- Automatic client cleanup on exit
- Refactor `test_ssh_connection()` to use it

**Test:** "Test SSH Connection" with verified cleanup

### 2.2 Ansible TQM Context Manager
**File:** `ansible/ansible_config.py`
**Work:**
- Add `ansible_task_queue_manager()` context manager
- Ensures TQM cleanup even on exceptions
- Refactor `ansible_ping_test()` to use it

**Test:** "Local Ansible Ping Test" with verified cleanup

## Phase 3: Command Pattern Refactoring

### 3.1 SSH Command Execution
**File:** `ssh_utils.py`
**Work:**
- Add `execute_ssh_command()` function
- Returns (success, stdout, stderr) tuple
- Consistent error handling
- Replace inline command execution in `test_ssh_connection()`

**Test:** "Test SSH Connection" executes all test commands

### 3.2 MockPopen Dispatch Dictionary
**File:** `utils/mocks/subprocess/popen.py`
**Work:**
- Create handler functions for each command type:
  - `_handle_echo_command()`
  - `_handle_mkdir_command()`
  - `_handle_test_command()`
  - `_handle_ansible_module()`
- Implement `COMMAND_HANDLERS` dispatch dictionary
- Simplify `communicate()` method

**Test:** "Local Ansible Ping Test" on iOS simulator

## Phase 4: Complex Function Breakdown

### 4.1 Simplify ansible_ping_test - Part 1
**File:** `ansible/ping.py`
**Work:**
- Extract configuration preparation:
  - `_prepare_ansible_config()` - paths and settings
  - `_setup_inventory()` - inventory and variable manager
- Original function reduced by ~40 lines

**Test:** "Local Ansible Ping Test" maintains functionality

### 4.2 Simplify ansible_ping_test - Part 2
**File:** `ansible/ping.py`
**Work:**
- Extract remaining logic:
  - `_configure_ansible_environment()` - context and plugins
  - `_execute_ping_test()` - actual test execution
  - `_report_results()` - result formatting
- Main function becomes a simple orchestrator

**Test:** "Local Ansible Ping Test" complete workflow

### 4.3 Simplify test_ssh_connection
**File:** `ssh_utils.py`
**Work:**
- Extract into focused functions:
  - `_prepare_ssh_config()` - configuration setup
  - `_attempt_connection()` - connection logic
  - `_test_connection_commands()` - command execution
- Reduce main function to <30 lines

**Test:** "Test SSH Connection" all scenarios

## Phase 5: Ansible Common Patterns

### 5.1 Ansible Environment Setup
**File:** `ansible/ansible_config.py`
**Work:**
- Add `setup_ansible_environment()` combining:
  - DataLoader creation
  - Inventory setup
  - Variable manager
  - Context configuration
- Update all Ansible operations to use it

**Test:** Both "Local Ansible Ping Test" and "Create rtorrent Droplet"

### 5.2 Create ansible/common.py
**File:** `ansible/common.py` (new)
**Work:**
- Create common Ansible execution patterns:
  - `run_ansible_task()` - single task execution
  - `run_ansible_playbook_with_cleanup()` - playbook execution
- Refactor `ansible_ping_test()` to use `run_ansible_task()`

**Test:** "Local Ansible Ping Test" using new common function

## Phase 6: Final Cleanup

### 6.1 Background Task Pattern
**File:** `ui/components.py`
**Work:**
- Add `execute_background_task()` wrapper
- Standardize error handling for all background tasks
- Update all button callbacks in `app.py`

**Test:** All buttons maintain proper background execution

### 6.2 Remove Duplication
**Work:**
- Final sweep for any remaining duplication
- Update all imports
- Remove any dead code
- Ensure consistent patterns throughout

**Test:** Complete application functionality test

## Complexity Reduction Targets

| Function | Current Lines | Target Lines | Reduction |
|----------|--------------|--------------|-----------|
| `ansible_ping_test` | 152 | <30 | 80% |
| `test_ssh_connection` | 133 | <30 | 77% |
| `MockPopen.communicate` | 103 | <30 | 71% |
| `run_droplet_playbook` | 113 | <40 | 65% |
| `generate_ed25519_key` | 89 | <30 | 66% |

## Dependencies Between Phases

- Phase 1 must complete before Phase 2 (foundation needed)
- Phase 3.1 depends on Phase 2.1 (SSH context manager)
- Phase 4 depends on Phases 1-3 (uses all utilities)
- Phase 5 depends on Phase 4.1-4.2 (Ansible refactoring)
- Phase 6 can start after Phase 4
