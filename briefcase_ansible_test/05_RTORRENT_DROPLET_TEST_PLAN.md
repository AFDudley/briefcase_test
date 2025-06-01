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
1. **API Key Storage**: Uses file-based storage instead of environment variable
2. **SSH Key Name**: Hardcoded as `'briefcase_ansible'` vs playbook expects `ssh_key_name`
3. **Variable Mismatch**: Code uses `digitalocean_token` but playbook expects `api_token`
4. **Error Handling**: Limited error scenarios covered
5. **Cleanup**: No automatic droplet cleanup mechanism

## Prerequisites Setup

### Environment Variables Required
```bash
export DIGITALOCEAN_TOKEN="your_real_do_token"
export SSH_KEY_NAME="briefcase_ansible"  # Must match hardcoded value
```

### Digital Ocean Account Requirements
1. **API Token**: Full droplet management permissions
2. **SSH Key**: Upload public key to DO account with name `briefcase_ansible`
3. **rtorrent Snapshot**: Pre-built image named `remote-rtorrent-image`
4. **Account Limits**: Sufficient quota for s-1vcpu-1gb droplets (~$0.007/hour)
5. **Cost Budget**: Immediate cleanup after testing to minimize costs

### Files to Create
```bash
# Create API key file as expected by current implementation
mkdir -p src/briefcase_ansible_test/resources/api_keys/
echo "your_real_do_token" > src/briefcase_ansible_test/resources/api_keys/do.api_key
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

#### 2.3 Test Case 3: Missing SSH Key
**Scenario**: SSH key 'briefcase_ansible' not found in DO account  
**Expected**: SSH key lookup failure in playbook execution  
**Steps**:
1. Ensure SSH key doesn't exist in DO account (or use different name)
2. Click button
3. Verify error in Ansible task execution

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

#### 3.1 Current Code Issues to Address
Based on analysis of `droplet_management.py`:

1. **Variable Name Mismatch**:
   - Code sets: `'digitalocean_token': api_key`
   - Playbook expects: `api_token: "{{ lookup('env', 'DIGITALOCEAN_TOKEN') }}"`
   - **Fix**: Change extra_vars to use `'api_token': api_key`

2. **SSH Key Name Mismatch**:
   - Code sets: `'ssh_key': 'briefcase_ansible'`
   - Playbook expects: `ssh_key_name` variable
   - **Fix**: Change to `'ssh_key_name': 'briefcase_ansible'`

#### 3.2 Recommended Code Fixes
```python
# In droplet_management.py line 59-62, change:
variable_manager.extra_vars = {
    'api_token': api_key,        # Changed from 'digitalocean_token'
    'ssh_key_name': 'briefcase_ansible'  # Changed from 'ssh_key'
}
```

#### 3.3 Enhanced Error Handling
Add specific error handling for:
- DO API rate limits
- Insufficient account quota
- Snapshot not found
- SSH key not found
- Network timeouts

### Phase 4: Testing Execution Steps

#### 4.1 Pre-Test Setup
```bash
# 1. Backup current code
git stash  # Save any changes

# 2. Create API key file
mkdir -p src/briefcase_ansible_test/resources/api_keys/
echo "dop_v1_your_actual_token_here" > src/briefcase_ansible_test/resources/api_keys/do.api_key

# 3. Verify DO account prerequisites
# - SSH key 'briefcase_ansible' uploaded
# - Snapshot 'remote-rtorrent-image' exists
# - Account has droplet quota

# 4. Deploy to simulator
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
- [ ] **Timeout Handling**: 5-minute timeout works properly
- [ ] **Cost Control**: Immediate droplet cleanup capability

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
- **Limited Scope**: Test one scenario at a time
- **Error Recovery**: Plan for stuck processes
- **Network Issues**: Test timeout handling

### Security Considerations
- **API Key Protection**: Don't commit real tokens to git
- **Key Rotation**: Use temporary/testing API keys where possible
- **Access Control**: Verify minimal required permissions

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