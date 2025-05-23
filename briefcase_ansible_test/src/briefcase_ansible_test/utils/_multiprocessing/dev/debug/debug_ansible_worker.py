#!/usr/bin/env python3
"""
Debug script to identify the specific issue with Ansible WorkerProcess.
"""

import sys
import traceback

# Set up path and patches
sys.path.insert(0, "src")
from briefcase_ansible_test.utils._multiprocessing import _patch_system_modules

_patch_system_modules()

from briefcase_ansible_test.utils.system_utils import (
    setup_pwd_module_mock,
    setup_grp_module_mock,
    patch_getpass,
)

setup_pwd_module_mock()
setup_grp_module_mock()
patch_getpass()

print("Testing direct import of Ansible WorkerProcess...")

try:
    # Import step by step to isolate the issue
    print("1. Importing multiprocessing...")
    import multiprocessing

    print(f"   multiprocessing: {multiprocessing}")

    print("2. Testing basic Process...")
    p = multiprocessing.Process(target=lambda: None)
    print(f"   Process created: {p}")

    print("3. Importing ansible.executor.process.worker...")
    from ansible.executor.process.worker import WorkerProcess

    print(f"   WorkerProcess imported: {WorkerProcess}")

    print("4. Testing WorkerProcess creation...")
    # Try to create a WorkerProcess instance
    wp = WorkerProcess(None, None, None, None, None, None, None, None)
    print(f"   WorkerProcess created: {wp}")

except Exception as e:
    print(f"Error occurred: {e}")
    print("Full traceback:")
    traceback.print_exc()

    # Try to find the exact source of the error
    print("\nDebugging method resolution...")
    import multiprocessing

    # Check if it's a method binding issue
    p = multiprocessing.Process(target=lambda: None)
    print(f"Process instance: {p}")

    # Look at the methods
    for attr_name in ["start", "join", "terminate", "is_alive"]:
        attr = getattr(p, attr_name)
        print(f"{attr_name}: {attr} (type: {type(attr)})")
