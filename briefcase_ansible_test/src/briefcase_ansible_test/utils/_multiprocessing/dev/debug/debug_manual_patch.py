#!/usr/bin/env python3
"""
Debug with manual patching control to test play execution.
"""

import sys
import threading
import time

sys.path.insert(0, "src")

print("🔍 Testing with manual patching control...")

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

# Manually patch multiprocessing
print("Step 1: Manually patching multiprocessing...")
from briefcase_ansible_test.utils._multiprocessing import _patch_system_modules

_patch_system_modules()
print("✅ Multiprocessing patched")

# Now test Ansible
print("Step 2: Importing Ansible with our multiprocessing...")
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.loader import init_plugin_loader
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible import context
from ansible.module_utils.common.collections import ImmutableDict
from ansible.playbook.play import Play

print("✅ Ansible imported")

print("Step 3: Setting up Ansible...")
init_plugin_loader()
context.CLIARGS = ImmutableDict(
    {
        "connection": "local",
        "forks": 1,
        "verbosity": 0,
    }
)

loader = DataLoader()
inventory = InventoryManager(loader=loader, sources=["localhost,"])
variable_manager = VariableManager(loader=loader, inventory=inventory)
print("✅ Ansible setup complete")

print("Step 4: Creating play and TaskQueueManager...")
play_source = {
    "name": "Manual Patch Test",
    "hosts": "localhost",
    "gather_facts": "no",
    "tasks": [
        {"name": "Simple debug", "debug": {"msg": "Hello from manual patch test"}}
    ],
}

play = Play().load(play_source, variable_manager=variable_manager, loader=loader)
print("✅ Play created")

tqm = TaskQueueManager(
    inventory=inventory,
    variable_manager=variable_manager,
    loader=loader,
    passwords={},
)
print("✅ TaskQueueManager created")

print("Step 5: Testing play execution...")


def execute_with_monitoring():
    """Execute play with monitoring."""
    execution_done = threading.Event()
    execution_result = []
    execution_error = []

    def monitor():
        start_time = time.time()
        while not execution_done.is_set():
            elapsed = time.time() - start_time
            thread_count = threading.active_count()
            thread_names = [t.name for t in threading.enumerate()]
            print(f"    ⏳ [{elapsed:.1f}s] {thread_count} threads: {thread_names}")

            if elapsed > 25:  # 25 second timeout
                print("    ⏰ TIMEOUT - execution appears hung")
                break

            if execution_done.wait(timeout=2):
                break

    def execute():
        try:
            print("  📝 Calling tqm.run(play)...")
            result = tqm.run(play)
            execution_result.append(result)
            execution_done.set()
            print(f"  ✅ Execution completed! Result: {result}")
        except Exception as e:
            execution_error.append(e)
            execution_done.set()
            print(f"  ❌ Execution failed: {e}")
            import traceback

            traceback.print_exc()

    monitor_thread = threading.Thread(target=monitor, daemon=True)
    execution_thread = threading.Thread(target=execute, name="PlayExecution")

    monitor_thread.start()
    execution_thread.start()

    execution_thread.join(timeout=30)

    if execution_thread.is_alive():
        print("  ⏰ Execution thread still alive - HANG CONFIRMED")
        return False, "hung"
    elif execution_result:
        return True, execution_result[0]
    elif execution_error:
        return False, execution_error[0]
    else:
        return False, "unknown"


success, result = execute_with_monitoring()

if success:
    print(f"\n🎉 SUCCESS: Play executed with result: {result}")
else:
    print(f"\n❌ FAILURE: Execution failed/hung: {result}")

# Cleanup
print("\nStep 6: Cleanup...")
try:
    tqm.cleanup()
    print("✅ Cleanup completed")
except Exception as e:
    print(f"❌ Cleanup failed: {e}")

print("\n🏁 Manual patch test complete")
