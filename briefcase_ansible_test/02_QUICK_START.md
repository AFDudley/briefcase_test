# Quick Start Guide

## First Time Setup

1. **Clone repository** (if not already done)
2. **Install dependencies**:
   ```bash
   pip install briefcase
   pip install -e .
   ```
3. **Run the app** using the automated script:
   ```bash
   ./test_changes.sh
   ```
4. **Note the bundle ID** and log file path from script output

## For Development Sessions

1. **Start fresh** (see _02_AI_CONTEXT_MANAGEMENT.md if needed)
2. **Identify current task** (Digital Ocean integration testing)
3. **Make changes** following 03_CODING_STANDARDS.md
4. **Test immediately** using `./test_changes.sh`
5. **Verify success** using 04_TESTING_STRATEGY.md
6. **Commit if successful**: 
   ```bash
   git add -u
   git commit -m "feat: [description]"
   ```

## Common Issues and Solutions

### App Won't Launch
- Check Xcode console for errors
- Verify iOS Simulator is running
- Try `briefcase build iOS` first

### Can't Find Logs
```bash
# Find app container
find ~/Library/Developer/CoreSimulator/Devices/*/data/Containers/Data/Application -name "briefcase_ansible_test*" -type d

# Then navigate to app/logs/ subdirectory
```

### Import Errors
- Ensure you're using the correct Python environment
- Check that all dependencies are installed
- Verify file paths match expected structure

### Test Failures After Changes
```bash
# Immediate rollback
git reset --hard HEAD

# Or if you want to debug, stash changes
git stash
# Test original code
# Then restore to continue debugging
git stash pop
```

## Key Commands Reference

### Running the App
```bash
briefcase dev              # Development mode (macOS)
briefcase run iOS          # iOS Simulator
```

### Code Quality Checks
```bash
black src/                 # Format code
flake8 src/               # Check style
pyright src/              # Type checking
```

### Testing with ios-interact
See full commands in 04_TESTING_STRATEGY.md, but basics:
- Launch app
- Take screenshot
- Click button by text
- Verify output

## Before Starting Any Work

Always check:
1. Current git status is clean
2. App runs successfully before changes
3. You have the correct phase documentation open
4. You understand the success criteria

## Getting Help

- Review error messages in Xcode console
- Check app logs for detailed stack traces
- Refer to specific phase documentation
- Use rollback strategy if needed