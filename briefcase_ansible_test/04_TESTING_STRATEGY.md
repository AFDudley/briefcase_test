# Testing Strategy - iOS Simulator with ios-interact

## Overview

This document describes how each refactoring phase will be tested using the ios-interact MCP server to ensure functionality is preserved throughout the refactoring process.

## Testing Environment

- **Platform:** iOS Simulator
- **Tool:** ios-interact MCP server
- **App Bundle ID:** To be determined from Xcode build
- **Test Data:** Existing inventory and playbook files in resources/
- **Log Files:** Available at `~/Library/Developer/CoreSimulator/Devices/[DEVICE_ID]/data/Containers/Data/Application/[APP_ID]/app/logs/`

## General Testing Flow

For each code change:

1. **Pre-change Baseline**
   - Take screenshot of current functionality
   - Document current output/behavior
   
2. **Make Code Changes**
   - Implement the refactoring
   - Ensure code compiles

3. **Deploy and Test**
   - Rebuild app if needed
   - Launch in simulator
   - Execute relevant functionality
   - Capture results

4. **Verification**
   - Compare output with baseline
   - Verify no functionality lost
   - Check for performance improvements

## Using test_changes.sh Script

### When to Use
The `test_changes.sh` script should be used after making any code changes to quickly rebuild, deploy, and prepare for testing. It automates the entire briefcase build pipeline.

### How to Use
```bash
# After making code changes, run:
./test_changes.sh

# The script will:
# 1. Find the booted iOS simulator
# 2. Run briefcase create/update/build
# 3. Launch the app
# 4. Output the log file path for testing
```

### Script Output
The script provides:
- Device ID of the booted simulator
- App bundle path (for accessing resources)
- Log file path (for checking detailed output)

### Example Testing Workflow
```bash
# 1. Make code changes
# Edit files as needed

# 2. Run the test script
./test_changes.sh

# 3. Use the log file path provided to monitor output
# Example: /Users/.../app/briefcase_ansible_test/logs/briefcase_ansible_test_*.log

# 4. Use ios-interact MCP to test functionality
# Take screenshots, click buttons, verify output
```

### Benefits
- No need to remember briefcase command sequence
- Automatically handles app rebuild and deployment
- Provides exact log file location using xcrun
- Runs app in background to avoid log following issues
- Single command to go from code change to testable app

## ios-interact Commands Reference

```python
# Launch app
mcp__ios-interact__launch_app(bundle_id="com.example.briefcase-ansible-test")

# Take screenshot
mcp__ios-interact__screenshot(filename="phase_1_1_before.png")

# Click button by text
mcp__ios-interact__click_text(text="Test SSH Connection")

# Find text in simulator (verify output)
mcp__ios-interact__find_text_in_simulator(search_text="✓ SSH Connection successful")

# Terminate app (for fresh restart)
mcp__ios-interact__terminate_app(bundle_id="com.example.briefcase-ansible-test")
```

## Accessing iOS Simulator Logs

The app writes detailed logs to the iOS simulator's filesystem. These can be accessed directly:

### Finding Log Files
```bash
# Find the simulator device ID
xcrun simctl list devices booted

# Navigate to app's container directory
cd ~/Library/Developer/CoreSimulator/Devices/[DEVICE_ID]/data/Containers/Data/Application/

# Find the app by bundle ID
find . -name "briefcase_ansible_test*" -type d

# Access logs
cd [APP_ID]/app/logs/
ls -la briefcase_ansible_test_*.log
```

### Log Analysis During Testing
```bash
# Tail the latest log during test execution
tail -f briefcase_ansible_test_*.log

# Search for specific errors
grep -i "error\|failed\|exception" briefcase_ansible_test_*.log

# Check iOS debug output
grep "iOS_DEBUG:" briefcase_ansible_test_*.log
```

### What to Look for in Logs
- **Error traces** not visible in UI
- **iOS_DEBUG** messages from multiprocessing
- **Import errors** during module loading
- **Timing information** for performance comparison
- **Full exception tracebacks**

## Phase-Specific Test Plans

### Phase 1.1: SSH Key Loading
**Test Steps:**
1. Screenshot current "Test SSH Connection" output
2. Implement `load_ssh_key()` refactoring
3. Rebuild and launch app
4. Click "Test SSH Connection (ed25519)"
5. Verify output shows:
   - "✓ Loaded ed25519 key successfully"
   - Connection attempt proceeds normally
6. Screenshot final result

**Success Criteria:**
- Key loads successfully
- Same output messages as before
- No new errors introduced

### Phase 1.2: Path Validation
**Test Steps:**
1. Launch app and click "Local Ansible Ping Test"
2. Document all path-related messages
3. Implement path validation utilities
4. Re-test "Local Ansible Ping Test"
5. Verify all paths found correctly:
   - Inventory file found
   - SSH key found
   - Playbook resources found

**Success Criteria:**
- All required files located
- Improved error messages for missing files
- No change in successful execution

### Phase 1.3: Status Reporter
**Test Steps:**
1. Click "Generate ED25519 Key"
2. Note current output format
3. Implement StatusReporter
4. Re-test key generation
5. Verify formatted output:
   - ✅ Success messages
   - ❌ Error messages (if any)
   - ⚠️ Warning messages (if any)

**Success Criteria:**
- Consistent status formatting
- All messages properly categorized
- Summary statistics available

### Phase 2.1: SSH Context Manager
**Test Steps:**
1. Run "Test SSH Connection" multiple times
2. Check for any resource leaks
3. Implement context manager
4. Re-test SSH connection
5. Force an error (wrong host) to test cleanup

**Success Criteria:**
- Connection works as before
- Proper cleanup on success
- Proper cleanup on failure
- No hanging connections

### Phase 2.2: Ansible TQM Context Manager
**Test Steps:**
1. Run "Local Ansible Ping Test"
2. Monitor for cleanup messages
3. Implement TQM context manager
4. Re-test with success scenario
5. Test with failure scenario (bad inventory)

**Success Criteria:**
- TQM cleanup always occurs
- No resource leaks
- Error handling maintained

### Phase 3.1: SSH Command Execution
**Test Steps:**
1. Run "Test SSH Connection"
2. Note all executed commands
3. Implement `execute_ssh_command()`
4. Re-test all commands:
   - `whoami`
   - `echo $SHELL`
   - `python3 --version`

**Success Criteria:**
- All commands execute
- Output captured correctly
- Error handling works

### Phase 3.2: MockPopen Dispatch
**Test Steps:**
1. Run "Local Ansible Ping Test" on iOS
2. Enable iOS debug output
3. Implement dispatch dictionary
4. Re-test on iOS simulator
5. Verify all command types handled:
   - echo commands
   - mkdir commands
   - ansible module execution

**Success Criteria:**
- Ansible ping succeeds on iOS
- All mock commands handled
- Cleaner code structure

### Phase 4: Complex Function Testing
**Test Each Extraction:**
1. Baseline screenshot
2. Extract one function
3. Test immediately
4. Verify identical behavior
5. Proceed to next extraction

**Critical Tests:**
- Ansible ping completes successfully
- All debug output preserved
- Error scenarios handled
- Performance not degraded

### Phase 5: Common Pattern Testing
**Integration Tests:**
1. Test all Ansible operations
2. Verify consistent behavior
3. Check for any timing issues
4. Validate error handling

### Phase 6: Final Testing
**Complete App Test:**
1. Click every button in sequence
2. Verify all functionality
3. Check for memory leaks
4. Performance comparison
5. Final screenshots

## Regression Test Suite

After each phase, run this minimal regression suite:

1. **SSH Test**: Click "Test SSH Connection" → Verify success
2. **Ansible Test**: Click "Local Ansible Ping Test" → Verify ping success
3. **Key Generation**: Click "Generate ED25519 Key" → Verify key created
4. **UI Responsiveness**: Verify no UI freezing during operations

## Error Injection Tests

For robust testing, deliberately cause errors:

1. **Missing File**: Rename inventory file → Verify graceful error
2. **Bad Permissions**: chmod 000 on key file → Verify error handling
3. **Network Issues**: Use non-existent host → Verify timeout handling
4. **iOS Specific**: Test iOS-specific paths → Verify proper mocking

## Using Logs in Testing Workflow

### Combined Testing Approach
1. **Visual Testing** - Use ios-interact for UI verification
2. **Log Analysis** - Check filesystem logs for hidden issues
3. **Correlation** - Match UI events with log timestamps

### Example Workflow
```bash
# 1. Start tailing logs before test
tail -f ~/Library/Developer/CoreSimulator/Devices/*/data/Containers/Data/Application/*/app/logs/briefcase_ansible_test_*.log &

# 2. Execute test via ios-interact
# (Click buttons, verify UI)

# 3. Check logs for issues not visible in UI
grep -A5 -B5 "ERROR\|CRITICAL" *.log

# 4. Verify successful operations
grep "UI OUTPUT: ✅" *.log | wc -l
```

## Documentation

For each test:
- Save "before" screenshot as `phase_X_Y_before.png`
- Save "after" screenshot as `phase_X_Y_after.png`
- Save relevant log excerpts showing errors or performance data
- Document any unexpected behavior
- Note performance improvements from log timestamps

## Success Metrics

- Zero functionality regressions
- Improved error messages
- Cleaner code structure verified
- All tests passing
- Performance maintained or improved