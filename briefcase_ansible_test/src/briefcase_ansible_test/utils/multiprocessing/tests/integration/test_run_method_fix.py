#!/usr/bin/env python3
"""
Test script to verify our run() method fix works correctly.
"""

import sys
import threading
import time

sys.path.insert(0, "src")

# Test our ThreadProcess directly first
from briefcase_ansible_test.utils.multiprocessing.process import ThreadProcess

print("Testing ThreadProcess run() method fix...")

# Test 1: Traditional target function usage
print("\n1. Testing target function usage:")


def test_function(message):
    print(f"Target function called with: {message}")
    return f"Result: {message}"


p1 = ThreadProcess(target=test_function, args=("hello",))
print(f"Created process: {p1}")
p1.start()
p1.join()
print(f"Exit code: {p1.exitcode}")
try:
    result = p1.get_result()
    print(f"Result: {result}")
except Exception as e:
    print(f"Error getting result: {e}")

# Test 2: Subclass with overridden run method (Ansible pattern)
print("\n2. Testing subclass run() method usage:")


class TestWorkerProcess(ThreadProcess):
    def __init__(self, message):
        super().__init__()  # No target provided
        self.message = message

    def run(self):
        print(f"Overridden run() called with: {self.message}")
        time.sleep(0.1)  # Simulate some work
        print(f"Overridden run() completing")
        return f"Worker result: {self.message}"


p2 = TestWorkerProcess("worker test")
print(f"Created worker process: {p2}")
p2.start()
p2.join()
print(f"Exit code: {p2.exitcode}")
try:
    result = p2.get_result()
    print(f"Result: {result}")
except Exception as e:
    print(f"Error getting result: {e}")

print("\n✅ ThreadProcess run() method tests completed!")

# Test 3: Quick Ansible WorkerProcess test
print("\n3. Testing actual Ansible WorkerProcess pattern:")

# Patch multiprocessing
from briefcase_ansible_test.utils.multiprocessing import _patch_system_modules

_patch_system_modules()

from briefcase_ansible_test.utils.system_utils import (
    setup_pwd_module_mock,
    setup_grp_module_mock,
    patch_getpass,
)

setup_pwd_module_mock()
setup_grp_module_mock()
patch_getpass()

try:
    from ansible.executor.process.worker import WorkerProcess

    print("Creating WorkerProcess to test inheritance...")

    # Create a minimal WorkerProcess instance
    wp = WorkerProcess(None, None, None, None, None, None, None, None)
    print(f"WorkerProcess created: {wp}")
    print(f"WorkerProcess has run method: {hasattr(wp, 'run')}")
    print(f"WorkerProcess.run is callable: {callable(getattr(wp, 'run', None))}")

    # Test that our ThreadProcess recognizes the overridden run method
    print(f"ThreadProcess._target is None: {wp._target is None}")
    print("✅ Ansible WorkerProcess pattern test completed!")

except Exception as e:
    print(f"❌ Error testing WorkerProcess: {e}")
    import traceback

    traceback.print_exc()

print("\n🎉 All tests completed!")
