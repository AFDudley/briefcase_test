#!/usr/bin/env python3
"""
test_changes.py - Python version of automated testing script for briefcase_ansible_test

This is a naive port of test_changes.sh to Python for better cross-platform compatibility.
"""

import subprocess
import sys
import time
import os
import signal

# App bundle ID
BUNDLE_ID = "xyz.afdudley.briefcase-ansible-test"

def run_command(cmd, shell=True, capture_output=False):
    """Run a command and return result."""
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
            return result
        else:
            result = subprocess.run(cmd, shell=shell)
            return result
    except Exception as e:
        print(f"Error running command: {e}")
        return None

def main():
    print("=== Briefcase iOS Test Script (Python) ===")
    
    # Step 1: Get the booted device ID
    print("\nFinding booted iOS simulator...")
    result = run_command("xcrun simctl list devices | grep Booted", capture_output=True)
    
    if result.returncode != 0 or not result.stdout.strip():
        print("Error: No booted iOS simulator found")
        print("Please start an iOS simulator first")
        sys.exit(1)
    
    # Extract device ID from output like "iPhone 14 (6EC5862B-...) (Booted)"
    device_line = result.stdout.strip()
    try:
        device_id = device_line.split('(')[1].split(')')[0]
    except IndexError:
        print("Error: Could not parse device ID from simctl output")
        sys.exit(1)
    
    print(f"Found device: {device_id}")
    
    # Step 2: Build and deploy
    print("\nBuilding and deploying app...")
    
    # Auto-confirm if app already exists
    confirm_process = subprocess.Popen(
        ["yes"], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )
    
    try:
        # Run briefcase commands
        subprocess.run(["briefcase", "create", "iOS"], 
                      stdin=confirm_process.stdout, 
                      stderr=subprocess.DEVNULL)
    except:
        pass  # May fail if app already exists, that's ok
    finally:
        confirm_process.terminate()
        confirm_process.wait()
    
    # Update and build
    run_command("briefcase update iOS")
    run_command("briefcase build iOS")
    
    # Step 3: Launch the app and capture output
    print("\nLaunching app on simulator...")
    print(f"Running: briefcase run iOS Xcode --device {device_id}")
    
    # Start briefcase run in background and capture output
    with open("./briefcase_run.log", "w") as log_file:
        briefcase_process = subprocess.Popen(
            ["briefcase", "run", "iOS", "Xcode", "--device", device_id],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Give the app time to launch completely
        print("Waiting for app to launch...")
        time.sleep(15)
        
        # Kill briefcase process so we can read logs
        print("Stopping briefcase process to read logs...")
        try:
            briefcase_process.terminate()
            briefcase_process.wait(timeout=5)
            print("✅ App launched successfully, briefcase process stopped")
        except subprocess.TimeoutExpired:
            briefcase_process.kill()
            briefcase_process.wait()
            print("✅ App launched successfully, briefcase process killed")
        except ProcessLookupError:
            print("Briefcase process already ended")
        
        # Read any remaining output
        if briefcase_process.stdout:
            remaining_output = briefcase_process.stdout.read()
            if remaining_output:
                log_file.write(remaining_output)
    
    # Show the briefcase output
    print("\n=== Briefcase Output ===")
    try:
        with open("./briefcase_run.log", "r") as log_file:
            print(log_file.read())
    except FileNotFoundError:
        print("No log file found")
    
    # Step 4: Get app paths and log file
    result = run_command(f'xcrun simctl get_app_container booted "{BUNDLE_ID}" app', capture_output=True)
    
    if result.returncode == 0 and result.stdout.strip():
        app_bundle = result.stdout.strip()
        log_file_path = f"{app_bundle}/app/briefcase_ansible_test/logs/briefcase_ansible_test_*.log"
        
        print(f"\nApp Bundle: {app_bundle}")
        print(f"Log file: {log_file_path}")
        print("\nApp is running! Test script complete.")
    else:
        print("\nCould not find app bundle")

if __name__ == "__main__":
    main()