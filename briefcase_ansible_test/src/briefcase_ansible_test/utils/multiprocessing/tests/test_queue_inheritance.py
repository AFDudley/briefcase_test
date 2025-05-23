#!/usr/bin/env python3
"""
Test script to debug the queue inheritance issue.
"""

import sys

sys.path.insert(0, "src")

# Patch multiprocessing first
from briefcase_ansible_test.utils.multiprocessing import _patch_system_modules

_patch_system_modules()

# Test the specific inheritance pattern that Ansible uses
try:
    print("Testing multiprocessing.queues.Queue...")
    from multiprocessing.queues import Queue

    print(f"Queue class: {Queue}")

    # Test creating a subclass like Ansible does
    class TestQueue(Queue):
        def get(self, *args, **kwargs):
            result = super(TestQueue, self).get(*args, **kwargs)
            return result

    print("Creating TestQueue instance...")
    tq = TestQueue()
    print(f"TestQueue created: {tq}")

    print("Testing basic operations...")
    tq.put("test")
    result = tq.get()
    print(f"Put/get test: {result}")

    print("✓ Queue inheritance test passed")

except Exception as e:
    print(f"❌ Queue inheritance test failed: {e}")
    import traceback

    traceback.print_exc()
