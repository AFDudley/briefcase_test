#!/usr/bin/env python3
"""
Simple debugging to find the hanging issue without complex instrumentation.
"""

import sys
import threading
import time

sys.path.insert(0, "src")

print("🔍 Simple hang debugging...")

# Apply patches
print("Step 1: Applying patches...")
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
print("✅ Patches applied")

print("Step 2: Testing basic ThreadProcess...")
from briefcase_ansible_test.utils.multiprocessing.process import ThreadProcess


def test_func():
    print("  🔸 test_func running")
    time.sleep(0.1)
    return "done"


p = ThreadProcess(target=test_func, name="Test")
print("  📝 Starting process...")
p.start()
print("  📝 Joining process...")
p.join()
print(f"  ✅ Process completed with exit code: {p.exitcode}")

print("Step 3: Testing minimal Ansible imports one by one...")

steps = [
    (
        "TaskQueueManager",
        "from ansible.executor.task_queue_manager import TaskQueueManager",
    ),
    ("init_plugin_loader", "from ansible.plugins.loader import init_plugin_loader"),
    ("DataLoader", "from ansible.parsing.dataloader import DataLoader"),
    ("VariableManager", "from ansible.vars.manager import VariableManager"),
    ("InventoryManager", "from ansible.inventory.manager import InventoryManager"),
    ("context", "from ansible import context"),
    (
        "ImmutableDict",
        "from ansible.module_utils.common.collections import ImmutableDict",
    ),
]

for name, import_stmt in steps:
    print(f"  📝 Importing {name}...")
    try:
        exec(import_stmt)
        print(f"  ✅ {name} imported successfully")
    except Exception as e:
        print(f"  ❌ {name} import failed: {e}")
        sys.exit(1)

print("Step 4: Basic Ansible initialization...")
print("  📝 Calling init_plugin_loader()...")
init_plugin_loader()
print("  ✅ Plugin loader initialized")

print("  📝 Setting context...")
context.CLIARGS = ImmutableDict(
    {
        "connection": "local",
        "forks": 1,
        "verbosity": 0,
    }
)
print("  ✅ Context set")

print("  📝 Creating DataLoader...")
loader = DataLoader()
print("  ✅ DataLoader created")

print("  📝 Creating InventoryManager...")
inventory = InventoryManager(loader=loader, sources=["localhost,"])
print("  ✅ InventoryManager created")

print("  📝 Creating VariableManager...")
variable_manager = VariableManager(loader=loader, inventory=inventory)
print("  ✅ VariableManager created")

print("Step 5: The critical test - TaskQueueManager creation...")


def test_tqm_creation():
    """Test TQM creation with progress tracking."""
    print("  📝 About to create TaskQueueManager...")

    # Start a thread to monitor progress
    creation_started = threading.Event()
    creation_done = threading.Event()

    def monitor():
        creation_started.wait()
        start_time = time.time()
        while not creation_done.is_set():
            elapsed = time.time() - start_time
            print(f"    ⏳ TQM creation running for {elapsed:.1f}s...")
            if creation_done.wait(timeout=2):
                break

    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()

    try:
        creation_started.set()
        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            passwords={},
        )
        creation_done.set()
        print("  ✅ TaskQueueManager created successfully!")

        print("  📝 Testing cleanup...")
        tqm.cleanup()
        print("  ✅ Cleanup successful!")

        return True

    except Exception as e:
        creation_done.set()
        print(f"  ❌ TaskQueueManager creation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


success = test_tqm_creation()

if success:
    print("\n🎉 SUCCESS: No hanging detected in basic TaskQueueManager operations!")
    print("The issue must be in play execution specifically.")
else:
    print("\n❌ FAILURE: Hanging detected during TaskQueueManager creation.")

print("\n🏁 Simple debug complete")
