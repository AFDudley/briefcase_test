# rtorrent Droplet Testing Plan - Full Integration with Real Digital Ocean Resources

## Overview
This document outlines the comprehensive test plan for the "Create rtorrent Droplet" button in the briefcase_ansible_test iOS application. We will use **real Digital Ocean resources** (Phase 2A approach) for authentic testing while implementing careful cost control and cleanup procedures.

## Current State Analysis

### Existing Implementation
- **Button**: "Create rtorrent Droplet" exists in UI (`app.py` line 49-52)
- **Function**: `run_droplet_playbook()` in `ansible/droplet_management.py`
- **Playbook**: `resources/playbooks/start_rtorrent_droplet.yml`
- **API Key Method**: Reads from file `resources/api_keys/do.api_key` (not environment variable)
- **SSH Key**: Hardcoded as `'briefcase_ansible'` in extra_vars (line 61)

### Current Implementation Issues Identified
1. **API Key Storage**: Uses file-based storage instead of environment variable ✓ (correct for iOS)
2. **SSH Key Approach**: Hardcoded key name requires manual DO setup
3. **Variable Mismatch**: Code uses `digitalocean_token` but playbook expects `api_token`
4. **SSH Variable Mismatch**: Code uses `ssh_key` but playbook expects `ssh_key_name`
5. **Error Handling**: Limited error scenarios covered
6. **Cleanup**: No automatic droplet/key cleanup mechanism

### Improved Approach: Ephemeral SSH Keys
Instead of requiring pre-existing SSH keys in DO account, the app should:
1. **Generate ephemeral SSH key pair** using existing `generate_ed25519_key()` function
2. **Upload key to DO** via API with unique name (e.g., `rtorrent-{timestamp}`)
3. **Create droplet** with the generated key
4. **Store private key** for droplet access
5. **Clean up** both droplet and SSH key when done

## Prerequisites Setup

### iOS-Compatible Configuration
**Note**: Environment variables are NOT available in iOS apps. The implementation correctly uses file-based configuration.

### Digital Ocean Account Requirements
1. **API Token**: Full droplet management permissions (including SSH key management)
2. **rtorrent Snapshot**: Pre-built image named `remote-rtorrent-image`
3. **Account Limits**: Sufficient quota for s-1vcpu-1gb droplets (~$0.007/hour)
4. **Cost Budget**: Immediate cleanup after testing to minimize costs
5. **SSH Key**: No pre-existing key required - app will generate ephemeral keys

### Required Files to Create
```bash
# Create API key file (iOS-compatible approach)
mkdir -p src/briefcase_ansible_test/resources/api_keys/
echo "dop_v1_your_actual_token_here" > src/briefcase_ansible_test/resources/api_keys/do.api_key

# Note: Replace with your actual Digital Ocean API token
# Token format: dop_v1_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Test Execution Plan

### Phase 1: Pre-Test Verification

#### 1.1 Verify Current Implementation
- [x] **Analysis Complete**: Current code reads API key from file, uses hardcoded SSH key name
- [ ] **API Key File**: Create `do.api_key` file with real token
- [ ] **SSH Key Upload**: Verify `briefcase_ansible` key exists in DO account
- [ ] **Snapshot Check**: Confirm `remote-rtorrent-image` snapshot exists

#### 1.2 Environment Setup
```bash
# 1. Navigate to project
cd /Users/rix/code/briefcase_test/briefcase_ansible_test

# 2. Create API key file
mkdir -p src/briefcase_ansible_test/resources/api_keys/
echo "your_do_token_here" > src/briefcase_ansible_test/resources/api_keys/do.api_key

# 3. Verify SSH key in DO account matches 'briefcase_ansible'

# 4. Build and deploy app
./test_changes.sh
```

### Phase 2: Test Scenarios

#### 2.1 Test Case 1: Missing API Key File
**Scenario**: API key file doesn't exist  
**Expected**: Clear error message "❌ API key file not found"  
**Steps**:
1. Remove/rename `do.api_key` file
2. Click "Create rtorrent Droplet" button
3. Verify error handling in logs

#### 2.2 Test Case 2: Invalid API Token
**Scenario**: API key file contains invalid token  
**Expected**: Authentication error from Digital Ocean API  
**Steps**:
1. Replace `do.api_key` content with invalid token
2. Click button
3. Monitor logs for API authentication errors

#### 2.3 Test Case 3: SSH Key Generation/Upload
**Scenario**: Test ephemeral SSH key generation and upload  
**Expected**: Successful key generation, upload to DO, and use in droplet  
**Steps**:
1. Valid API token and snapshot exist
2. Click button
3. Verify SSH key generated and uploaded with timestamp name
4. Verify droplet created with same name as key

#### 2.4 Test Case 4: Missing rtorrent Snapshot
**Scenario**: No snapshot named 'remote-rtorrent-image'  
**Expected**: Snapshot lookup failure  
**Steps**:
1. Ensure no matching snapshot exists in DO account
2. Click button
3. Verify error in playbook execution

#### 2.5 Test Case 5: Successful Droplet Creation
**Scenario**: All prerequisites met  
**Expected**: Successful droplet creation with connection details  
**Steps**:
1. Ensure valid API key, SSH key, and snapshot exist
2. Click button
3. Monitor 5-minute timeout for completion
4. Verify droplet creation in DO console
5. **IMPORTANT**: Immediately destroy droplet to prevent charges

#### 2.6 Test Case 6: Network Connectivity Issues
**Scenario**: Simulate network problems  
**Expected**: Timeout or connection error handling  
**Steps**:
1. Test with network restrictions if possible
2. Verify timeout handling (300 seconds)

### Phase 3: Implementation Improvements

#### 3.1 Critical Code Issues to Fix
Based on analysis of `droplet_management.py` vs `start_rtorrent_droplet.yml`:

1. **Variable Name Mismatch**:
   - Code sets: `'digitalocean_token': api_key`
   - Playbook expects: `api_token` variable
   - **Fix**: Change extra_vars to use `'api_token': api_key`

2. **SSH Key Variable Mismatch**:
   - Code sets: `'ssh_key': 'briefcase_ansible'`
   - Playbook expects: `ssh_key_name` variable
   - **Fix**: Change to `'ssh_key_name': 'briefcase_ansible'`

3. **Environment Variable Issue**:
   - Playbook tries: `{{ lookup('env', 'DIGITALOCEAN_TOKEN') }}`
   - iOS Reality: Environment variables not available
   - **Fix**: Playbook must rely on extra_vars, not environment lookup

#### 3.2 Required Code Fixes - Basic
```python
# Minimum fix in droplet_management.py lines 59-62:
variable_manager.extra_vars = {
    'api_token': api_key,                    # Fixed variable name
    'ssh_key_name': 'briefcase_ansible'      # Fixed variable name
}
```

#### 3.3 Enhanced Implementation - Ephemeral Keys
```python
# Better approach with ephemeral SSH keys:
import time
from briefcase_ansible_test.ssh_utils import generate_ed25519_key

# Generate ephemeral SSH key
success, private_key_path, public_key_path, public_key_str = generate_ed25519_key(
    app_paths.app, ui_updater
)

# Create unique name for both key and droplet
timestamp = int(time.time())
resource_name = f"rtorrent-{timestamp}"

# Pass to playbook
variable_manager.extra_vars = {
    'api_token': api_key,
    'droplet_name': resource_name,      # Same name for droplet
    'ssh_key_name': resource_name,      # Same name for SSH key
    'ssh_public_key': public_key_str,
    'cleanup_ssh_key': True  # Flag for cleanup
}
```

#### 3.4 Playbook Enhancement Required
Add SSH key upload task before droplet creation:
```yaml
- name: Upload ephemeral SSH key to Digital Ocean
  community.digitalocean.digital_ocean_sshkey:
    oauth_token: "{{ api_token }}"
    name: "{{ ssh_key_name }}"
    ssh_pub_key: "{{ ssh_public_key }}"
    state: present
  register: ssh_key_result

- name: Use key ID for droplet creation
  set_fact:
    ssh_key_id: "{{ ssh_key_result.data.ssh_key.id }}"
```

#### 3.3 Enhanced Error Handling
Add specific error handling for:
- DO API rate limits
- Insufficient account quota
- Snapshot not found
- SSH key not found
- Network timeouts

#### 3.5 Cleanup Implementation
Add cleanup playbook or tasks to remove both droplet and SSH key:
```yaml
- name: Destroy rtorrent droplet
  community.digitalocean.digital_ocean_droplet:
    oauth_token: "{{ api_token }}"
    name: "{{ droplet_name }}"
    state: absent
    
- name: Remove ephemeral SSH key
  community.digitalocean.digital_ocean_sshkey:
    oauth_token: "{{ api_token }}"
    name: "{{ ssh_key_name }}"
    state: absent
```

### Phase 4: Testing Execution Steps

#### 4.1 Pre-Test Setup
```bash
# 1. Backup current code
git stash  # Save any changes

# 2. Implement ephemeral key approach (or apply basic fixes)
# Option A: Implement full ephemeral key solution
# Option B: Apply minimum variable name fixes

# 3. Create API key file
mkdir -p src/briefcase_ansible_test/resources/api_keys/
echo "dop_v1_your_actual_token_here" > src/briefcase_ansible_test/resources/api_keys/do.api_key

# 4. Verify DO account prerequisites
# - API token has SSH key management permissions
# - Snapshot 'remote-rtorrent-image' exists in DO account
# - Account has sufficient droplet quota
# - NO pre-existing SSH key required (ephemeral approach)

# 5. Deploy to simulator
./test_changes.sh
```

#### 4.2 Test Execution Sequence
1. **Test 1**: Missing API key (remove file, test, restore)
2. **Test 2**: Invalid API key (corrupt file, test, fix)
3. **Test 3**: Valid setup - **CRITICAL DROPLET CREATION TEST**
4. **Test 4**: Immediate cleanup verification

#### 4.3 Log Monitoring
Monitor iOS simulator logs at:
```
/Users/rix/Library/Developer/CoreSimulator/Devices/[device-id]/data/Containers/Bundle/Application/[app-id]/briefcase_ansible_test.app/app/briefcase_ansible_test/logs/
```

Watch for:
- Ansible task execution
- Digital Ocean API responses
- Error messages and stack traces
- Timeout handling
- Variable passing

### Phase 5: Success Criteria

#### 5.1 Required Outcomes
- [ ] **Button Functionality**: No app crashes, responsive UI
- [ ] **Error Handling**: Clear messages for all failure scenarios
- [ ] **API Integration**: Successful communication with Digital Ocean
- [ ] **Ansible Execution**: Playbook runs correctly in iOS environment
- [ ] **Variable Passing**: Correct parameter transmission to playbook
- [ ] **Ephemeral Resources**: SSH key generated, uploaded, and used successfully
- [ ] **Resource Naming**: Droplet and SSH key share same timestamp-based name
- [ ] **Timeout Handling**: 5-minute timeout works properly
- [ ] **Cost Control**: Automatic cleanup of both droplet and SSH key

#### 5.2 Deliverables
1. **Test Results Report**: Detailed results for all test cases
2. **Code Fixes**: Corrected variable names and error handling
3. **Log Analysis**: Complete iOS simulator log review
4. **Cost Report**: Actual Digital Ocean charges incurred
5. **Documentation Update**: Usage instructions and known issues

## Risk Mitigation

### Cost Control Measures
- **Immediate Cleanup**: Destroy droplets within minutes of creation
- **Smallest Size**: Use s-1vcpu-1gb droplets only (~$0.007/hour)
- **Time Limits**: Set strict testing windows
- **Monitoring**: Track DO account charges during testing

### Technical Risk Mitigation
- **Code Backup**: Git stash before modifications
- **Variable Fix Required**: Must fix variable name mismatches before testing
- **Limited Scope**: Test one scenario at a time
- **Error Recovery**: Plan for stuck processes
- **iOS Environment**: No environment variables available, file-based only

### Security Considerations
- **API Key Protection**: Don't commit real tokens to git (add `*.api_key` to .gitignore)
- **Key Rotation**: Use temporary/testing API keys where possible
- **Access Control**: Verify minimal required permissions
- **File Permissions**: Ensure API key file is readable by app

## Expected Timeline
- **Setup**: 30 minutes (API key, SSH key verification)
- **Testing**: 60 minutes (all test scenarios)
- **Analysis**: 30 minutes (log review, results documentation)
- **Cleanup**: 15 minutes (droplet destruction, cost verification)
- **Total**: 2.5 hours

## Next Steps
1. **Immediate**: Verify Digital Ocean account prerequisites
2. **Setup**: Create API key file and deploy to simulator
3. **Execute**: Run test scenarios in sequence
4. **Document**: Capture results and logs
5. **Optimize**: Implement any necessary code fixes
6. **Report**: Provide comprehensive test results

This plan ensures thorough testing of the rtorrent droplet functionality while maintaining strict cost control and proper documentation of results.