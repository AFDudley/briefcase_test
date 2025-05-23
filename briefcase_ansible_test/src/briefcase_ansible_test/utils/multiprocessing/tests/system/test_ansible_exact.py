#!/usr/bin/env python3
"""
Test script that replicates the exact Ansible WorkerProcess inheritance pattern.
"""

import sys

sys.path.insert(0, "src")

# Apply all patches
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
    print("Testing exact Ansible pattern...")

    # Replicate Ansible's imports
    from multiprocessing.queues import Queue
    from ansible.utils.multiprocessing import context as multiprocessing_context

    print(f"multiprocessing_context: {multiprocessing_context}")
    print(f"multiprocessing_context.Process: {multiprocessing_context.Process}")

    # Replicate WorkerQueue
    class WorkerQueue(Queue):
        """Queue that raises AnsibleError items on get()."""

        def get(self, *args, **kwargs):
            result = super(WorkerQueue, self).get(*args, **kwargs)
            return result

    print("WorkerQueue created successfully")

    # Replicate WorkerProcess
    class WorkerProcess(multiprocessing_context.Process):
        def __init__(self, *args, **kwargs):
            super(WorkerProcess, self).__init__()
            print("WorkerProcess.__init__ called")

    print("Creating WorkerProcess...")
    wp = WorkerProcess()
    print(f"WorkerProcess created: {wp}")

    print("✓ Exact Ansible pattern test passed")

except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback

    traceback.print_exc()

    # Get more specific error info
    print("\nDumping multiprocessing_context details:")
    try:
        from ansible.utils.multiprocessing import context as multiprocessing_context

        print(f"Context type: {type(multiprocessing_context)}")
        print(f"Context attributes: {dir(multiprocessing_context)}")
        print(f"Process class: {multiprocessing_context.Process}")
        print(f"Process MRO: {multiprocessing_context.Process.__mro__}")
    except Exception as e2:
        print(f"Error getting context details: {e2}")
