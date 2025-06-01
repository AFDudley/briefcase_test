# Testing Strategy - iOS Simulator with ios-interact

## Overview

This document describes how to test new features and integrations using the ios-interact MCP server, with primary focus on Digital Ocean integration testing for the distributed torrent architecture.

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

## Digital Ocean Integration Test Plans

### Primary Test: rtorrent Droplet Creation
**Objective:** Validate full Digital Ocean integration for distributed torrent architecture

**Prerequisites:**
- Valid Digital Ocean API token
- SSH key uploaded to DO account (name: 'briefcase_ansible')
- Pre-built rtorrent snapshot ('remote-rtorrent-image')
- Account quota for s-1vcpu-1gb droplets

**Test Cases:**

#### Test 1: Missing API Key
**Steps:**
1. Ensure no `do.api_key` file exists
2. Click "Create rtorrent Droplet"
3. Verify error message: "❌ API key file not found"

#### Test 2: Invalid API Token
**Steps:**
1. Create `do.api_key` with invalid token
2. Click "Create rtorrent Droplet"
3. Monitor for Digital Ocean authentication errors

#### Test 3: Missing SSH Key
**Steps:**
1. Use valid API token but wrong SSH key name
2. Click "Create rtorrent Droplet"
3. Verify SSH key lookup failure in Ansible execution

#### Test 4: Missing Snapshot
**Steps:**
1. Valid API/SSH setup but no rtorrent snapshot
2. Click "Create rtorrent Droplet"
3. Verify snapshot lookup failure

#### Test 5: Successful Droplet Creation
**Steps:**
1. Valid API token, SSH key, and snapshot
2. Click "Create rtorrent Droplet"
3. Monitor 5-minute timeout for completion
4. Verify droplet creation in Digital Ocean console
5. **CRITICAL:** Immediately destroy droplet

**Expected Success Output:**
- "✅ Digital Ocean API key loaded"
- "✅ Playbook found"
- "✅ Ansible components initialized"
- Ansible task execution progress
- "✅ Droplet creation completed successfully!"
- Connection details with IP address

### Secondary Tests: Core Functionality

#### Baseline Functionality Verification
1. **SSH Test**: "Test SSH Connection" → Verify simplified function works
2. **Ansible Test**: "Local Ansible Ping Test" → Verify ping success
3. **Key Generation**: "Generate ED25519 Key" → Verify streamlined output
4. **Generated Key Test**: "Test SSH Connection with Generated Key" → Verify integration

### Integration Workflow Test

**Complete User Journey:**
1. Generate SSH key in app
2. Upload public key to Digital Ocean manually
3. Create API key file with real token
4. Create rtorrent droplet
5. Verify droplet connectivity
6. Clean up resources

## Regression Test Suite

Before any Digital Ocean testing, verify core functionality:

1. **SSH Test**: Click "Test SSH Connection" → Verify simplified 24-line function
2. **Ansible Test**: Click "Local Ansible Ping Test" → Verify streamlined execution
3. **Key Generation**: Click "Generate ED25519 Key" → Verify concise output
4. **UI Responsiveness**: Verify no UI freezing during operations

## Error Injection Tests

For robust Digital Ocean testing:

1. **Missing API File**: Remove `do.api_key` → Verify graceful error
2. **Bad API Token**: Invalid token → Verify authentication error
3. **Network Issues**: Test timeout handling in droplet creation
4. **Account Limits**: Test quota exceeded scenarios
5. **Missing Resources**: Test missing SSH keys/snapshots in DO account

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