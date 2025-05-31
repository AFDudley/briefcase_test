#!/bin/bash

# test_changes.sh - Automated testing script for briefcase_ansible_test

set -e  # Exit on error

# App bundle ID
BUNDLE_ID="xyz.afdudley.briefcase-ansible-test"

echo "=== Briefcase iOS Test Script ==="

# Step 1: Get the booted device ID
echo -e "\nFinding booted iOS simulator..."
DEVICE_ID=$(xcrun simctl list devices | grep Booted | awk -F'[()]' '{print $2}')

if [ -z "$DEVICE_ID" ]; then
    echo "Error: No booted iOS simulator found"
    echo "Please start an iOS simulator first"
    exit 1
fi

echo "Found device: $DEVICE_ID"

# Step 2: Build and deploy
echo -e "\nBuilding and deploying app..."

# Use yes to auto-confirm if app already exists
yes | briefcase create iOS 2>/dev/null || true

briefcase update iOS
briefcase build iOS

# Step 3: Launch the app (in background to avoid log following)
echo -e "\nLaunching app on simulator..."
briefcase run iOS Xcode --device "$DEVICE_ID" > /dev/null 2>&1 &

# Give the app time to start
echo "Waiting for app to launch..."
sleep 5

# Step 4: Get app paths and log file
APP_BUNDLE=$(xcrun simctl get_app_container booted "$BUNDLE_ID" app 2>/dev/null)

if [ -z "$APP_BUNDLE" ]; then
    echo "Error: Could not find app bundle. Is the app installed?"
    exit 1
fi

LOG_FILE="$APP_BUNDLE/app/briefcase_ansible_test/logs/briefcase_ansible_test_*.log"

echo -e "\nApp Bundle: $APP_BUNDLE"
echo "Log file: $LOG_FILE"
echo -e "\nApp is running! Test script complete."