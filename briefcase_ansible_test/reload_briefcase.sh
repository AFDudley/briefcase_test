#!/bin/bash

# Get the booted device ID
DEVICE_ID=$(xcrun simctl list devices | grep Booted | awk -F'[()]' '{print $2}')

if [ -z "$DEVICE_ID" ]; then
    echo "Error: No booted iOS simulator found"
    exit 1
fi

echo "Found booted device: $DEVICE_ID"

# Run the briefcase commands
echo "Creating iOS project..."
briefcase create iOS

echo "Updating iOS project with code changes..."
briefcase update iOS

echo "Building iOS app..."
briefcase build iOS

echo "Running on device $DEVICE_ID..."
# Run in background and detach to avoid waiting for log output
briefcase run iOS Xcode --device "$DEVICE_ID" > /dev/null 2>&1 &
PID=$!
echo "App launched in background (PID: $PID)"
echo "Script completed successfully!"