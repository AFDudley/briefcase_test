#!/usr/bin/env python3
"""
Debug play execution specifically to find the hanging issue.
"""

import sys
import threading
import time
import signal

sys.path.insert(0, "src")


def timeout_handler(signum, frame):
    print("\n⏰ TIMEOUT: Process took too long")
    import traceback

    traceback.print_stack(frame)
    sys.exit(1)


# Set a 60-second timeout
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(60)

print("🔍 Debugging play execution...")

# Apply patches
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

# Set up Ansible
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

print("✅ Basic Ansible setup complete")

# Create a simple play
play_source = {
    "name": "Debug Test Play",
    "hosts": "localhost",
    "gather_facts": "no",
    "tasks": [{"name": "Simple debug task", "debug": {"msg": "Hello from debug task"}}],
}

play = Play().load(play_source, variable_manager=variable_manager, loader=loader)
print("✅ Play created")

# Create TaskQueueManager
tqm = TaskQueueManager(
    inventory=inventory,
    variable_manager=variable_manager,
    loader=loader,
    passwords={},
)
print("✅ TaskQueueManager created")


# Monitor threads during execution
def monitor_threads():
    """Monitor threads during play execution."""
    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        thread_count = threading.active_count()
        threads = []
        for t in threading.enumerate():
            thread_info = f"{t.name}({t.ident})"
            if hasattr(t, "_target") and t._target:
                thread_info += f"->{t._target.__name__}"
            threads.append(thread_info)

        print(f"[{elapsed:.1f}s] 🧵 {thread_count} threads: {threads}")
        time.sleep(1)


monitor_thread = threading.Thread(target=monitor_threads, daemon=True)
monitor_thread.start()

print("🚀 Starting play execution...")
print("   This is where the hang typically occurs")

# Execute in separate thread with detailed monitoring
execution_result = []
execution_error = []
execution_done = threading.Event()


def execute_play():
    """Execute the play and capture result."""
    try:
        print("  📝 Calling tqm.run(play)...")
        result = tqm.run(play)
        execution_result.append(result)
        print(f"  ✅ Play execution completed with result: {result}")
        execution_done.set()
    except Exception as e:
        execution_error.append(e)
        print(f"  ❌ Play execution failed: {e}")
        import traceback

        traceback.print_exc()
        execution_done.set()


execution_thread = threading.Thread(target=execute_play, name="PlayExecution")
execution_thread.start()

# Wait for completion or timeout
print("⏳ Waiting for play execution (timeout: 30s)...")
completed = execution_done.wait(timeout=30)

if completed:
    if execution_result:
        print(f"🎉 SUCCESS: Play completed with result {execution_result[0]}")
    elif execution_error:
        print(f"❌ FAILED: Play failed with error: {execution_error[0]}")
    else:
        print("❓ UNKNOWN: Execution completed but no result")
else:
    print("⏰ TIMEOUT: Play execution hung after 30 seconds")
    print("🔍 ANALYSIS: This confirms the hanging issue during play execution")

    # Print thread states
    print("\n📊 Thread states during hang:")
    for t in threading.enumerate():
        alive = "alive" if t.is_alive() else "dead"
        daemon = "daemon" if t.daemon else "normal"
        print(f"  - {t.name}: {alive}, {daemon}")

    # Check if our execution thread is still running
    if execution_thread.is_alive():
        print("  🔍 PlayExecution thread is still alive - likely blocked in tqm.run()")

# Cleanup
try:
    print("\n🧹 Cleaning up...")
    tqm.cleanup()
    print("✅ Cleanup completed")
except Exception as e:
    print(f"❌ Cleanup failed: {e}")

signal.alarm(0)  # Cancel timeout
print("\n🏁 Debug complete")
