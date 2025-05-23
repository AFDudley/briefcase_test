#!/usr/bin/env python3
"""
Debug the specific hanging issue during play execution.
"""

import sys
import threading
import time

sys.path.insert(0, "src")

print("🔍 Debugging play execution hang...")

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

# Quick setup (we know this works from previous test)
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.loader import init_plugin_loader
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible import context
from ansible.module_utils.common.collections import ImmutableDict
from ansible.playbook.play import Play

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

print("✅ Ansible setup complete (known working)")

# Create the simplest possible play
print("Step 2: Creating minimal play...")
play_source = {
    "name": "Minimal Test",
    "hosts": "localhost",
    "gather_facts": "no",
    "tasks": [{"name": "Debug message", "debug": {"msg": "Hello world"}}],
}

play = Play().load(play_source, variable_manager=variable_manager, loader=loader)
print("✅ Play created")

# Create TQM
print("Step 3: Creating TaskQueueManager...")
tqm = TaskQueueManager(
    inventory=inventory,
    variable_manager=variable_manager,
    loader=loader,
    passwords={},
)
print("✅ TaskQueueManager created")

print("Step 4: Testing play execution with monitoring...")


def test_play_execution():
    """Test play execution with detailed progress monitoring."""

    # Monitor during execution
    execution_started = threading.Event()
    execution_done = threading.Event()
    execution_result = []
    execution_error = []

    def monitor():
        execution_started.wait()
        start_time = time.time()
        max_wait = 30  # 30 second timeout

        while not execution_done.is_set():
            elapsed = time.time() - start_time
            thread_count = threading.active_count()
            thread_names = [t.name for t in threading.enumerate()]

            print(f"    ⏳ [{elapsed:.1f}s] {thread_count} threads: {thread_names}")

            if elapsed > max_wait:
                print(f"    ⏰ TIMEOUT after {max_wait}s - execution appears hung")
                break

            if execution_done.wait(timeout=2):
                break

    def execute_play():
        try:
            print("  📝 Calling tqm.run(play)...")
            result = tqm.run(play)
            execution_result.append(result)
            execution_done.set()
            print(f"  ✅ Play execution completed! Result: {result}")
        except Exception as e:
            execution_error.append(e)
            execution_done.set()
            print(f"  ❌ Play execution failed: {e}")
            import traceback

            traceback.print_exc()

    monitor_thread = threading.Thread(target=monitor, daemon=True)
    execution_thread = threading.Thread(target=execute_play, name="PlayExecution")

    monitor_thread.start()
    execution_started.set()
    execution_thread.start()

    # Wait for completion (monitor will timeout after 30s)
    execution_thread.join(timeout=35)

    if execution_thread.is_alive():
        print("  ⏰ Play execution thread is still alive after timeout")
        return False, "timeout"
    elif execution_result:
        return True, execution_result[0]
    elif execution_error:
        return False, execution_error[0]
    else:
        return False, "unknown"


print("  🚀 Starting monitored play execution...")
success, result = test_play_execution()

if success:
    print(f"\n🎉 SUCCESS: Play executed successfully with result: {result}")
    print("The hanging issue has been resolved!")
else:
    print(f"\n❌ FAILURE: Play execution failed/hung: {result}")
    print("The hanging issue persists during play execution.")

# Cleanup
print("\nStep 5: Cleanup...")
try:
    tqm.cleanup()
    print("✅ Cleanup completed")
except Exception as e:
    print(f"❌ Cleanup failed: {e}")

print("\n🏁 Play execution debug complete")
