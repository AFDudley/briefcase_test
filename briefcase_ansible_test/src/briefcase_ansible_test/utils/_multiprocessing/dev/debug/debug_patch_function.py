#!/usr/bin/env python3
"""
Debug the _patch_system_modules() function to find what's causing hangs.
"""

import sys
import threading
import time

sys.path.insert(0, "src")

print("🔍 Debugging patch function...")

# Apply system utils
from briefcase_ansible_test.utils.system_utils import (
    setup_pwd_module_mock,
    setup_grp_module_mock,
    patch_getpass,
)

setup_pwd_module_mock()
setup_grp_module_mock()
patch_getpass()
print("✅ System utils applied")

# Import our module without auto-patching
import briefcase_ansible_test.utils._multiprocessing as our_mp

print("Step 1: Testing individual patch components...")

# Save original modules
original_modules = {}
patch_targets = [
    "multiprocessing",
    "multiprocessing.process",
    "multiprocessing.queues",
    "multiprocessing.synchronize",
    "multiprocessing.context",
    "multiprocessing.pool",
]

for target in patch_targets:
    original_modules[target] = sys.modules.get(target)

print("Step 2: Patching main multiprocessing...")
sys.modules["multiprocessing"] = our_mp
print("✅ Main multiprocessing patched")

# Test Ansible import
print("  📝 Testing Ansible import...")
try:
    from ansible.executor.task_queue_manager import TaskQueueManager

    print("  ✅ TaskQueueManager imports fine with main patch only")
except Exception as e:
    print(f"  ❌ TaskQueueManager failed with main patch: {e}")

print("Step 3: Adding multiprocessing.process patch...")
sys.modules["multiprocessing.process"] = type(
    "Module",
    (),
    {
        "Process": our_mp.Process,
        "BaseProcess": our_mp.BaseProcess,
        "current_process": our_mp.current_process,
        "active_children": our_mp.active_children,
    },
)()
print("✅ multiprocessing.process patched")

print("  📝 Testing Ansible import after process patch...")
try:
    # Reload to pick up new patch
    if "ansible.executor.task_queue_manager" in sys.modules:
        del sys.modules["ansible.executor.task_queue_manager"]
    from ansible.executor.task_queue_manager import TaskQueueManager as TQM2

    print("  ✅ TaskQueueManager still works")
except Exception as e:
    print(f"  ❌ TaskQueueManager failed after process patch: {e}")

print("Step 4: Adding multiprocessing.queues patch...")
sys.modules["multiprocessing.queues"] = type(
    "Module",
    (),
    {
        "Queue": our_mp.Queue,
        "SimpleQueue": our_mp.SimpleQueue,
        "JoinableQueue": our_mp.JoinableQueue,
    },
)()
print("✅ multiprocessing.queues patched")

print("  📝 Testing Ansible import after queues patch...")
try:
    if "ansible.executor.task_queue_manager" in sys.modules:
        del sys.modules["ansible.executor.task_queue_manager"]
    from ansible.executor.task_queue_manager import TaskQueueManager as TQM3

    print("  ✅ TaskQueueManager still works")
except Exception as e:
    print(f"  ❌ TaskQueueManager failed after queues patch: {e}")

print("Step 5: Adding multiprocessing.synchronize patch...")
sys.modules["multiprocessing.synchronize"] = type(
    "Module",
    (),
    {
        "Lock": our_mp.Lock,
        "RLock": our_mp.RLock,
        "Semaphore": our_mp.Semaphore,
        "BoundedSemaphore": our_mp.BoundedSemaphore,
        "Event": our_mp.Event,
        "Condition": our_mp.Condition,
        "Barrier": our_mp.Barrier,
    },
)()
print("✅ multiprocessing.synchronize patched")

print("  📝 Testing Ansible import after synchronize patch...")
try:
    if "ansible.executor.task_queue_manager" in sys.modules:
        del sys.modules["ansible.executor.task_queue_manager"]
    from ansible.executor.task_queue_manager import TaskQueueManager as TQM4

    print("  ✅ TaskQueueManager still works")
except Exception as e:
    print(f"  ❌ TaskQueueManager failed after synchronize patch: {e}")

print("Step 6: Adding multiprocessing.context patch...")
sys.modules["multiprocessing.context"] = type(
    "Module",
    (),
    {
        "Process": our_mp.Process,
        "get_context": our_mp.get_context,
        "get_start_method": our_mp.get_start_method,
        "set_start_method": our_mp.set_start_method,
    },
)()
print("✅ multiprocessing.context patched")

print("  📝 Testing Ansible import after context patch...")
try:
    if "ansible.executor.task_queue_manager" in sys.modules:
        del sys.modules["ansible.executor.task_queue_manager"]
    from ansible.executor.task_queue_manager import TaskQueueManager as TQM5

    print("  ✅ TaskQueueManager still works")
except Exception as e:
    print(f"  ❌ TaskQueueManager failed after context patch: {e}")
    print("  🔍 This is likely where the hang occurs!")
    import traceback

    traceback.print_exc()

print("Step 7: Adding multiprocessing.pool patch...")
sys.modules["multiprocessing.pool"] = our_mp.pool
print("✅ multiprocessing.pool patched")

print("  📝 Testing Ansible import after pool patch...")
try:
    if "ansible.executor.task_queue_manager" in sys.modules:
        del sys.modules["ansible.executor.task_queue_manager"]
    from ansible.executor.task_queue_manager import TaskQueueManager as TQM6

    print("  ✅ TaskQueueManager still works after all patches")
except Exception as e:
    print(f"  ❌ TaskQueueManager failed after pool patch: {e}")

# Restore original modules
print("\nStep 8: Restoring original modules...")
for target, original in original_modules.items():
    if original is not None:
        sys.modules[target] = original
    elif target in sys.modules:
        del sys.modules[target]

print("\n🏁 Patch function debugging complete")
