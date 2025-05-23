#!/usr/bin/env python3
"""
Ultra-granular debugging to find exact hanging location.
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


# Set a 30-second timeout
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)

print("🔍 Ultra-granular debugging starting...")

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

print("Step 2: Testing imports...")
try:
    from ansible.executor.task_queue_manager import TaskQueueManager

    print("  ✅ TaskQueueManager imported")

    from ansible.plugins.loader import init_plugin_loader

    print("  ✅ init_plugin_loader imported")

    from ansible.parsing.dataloader import DataLoader

    print("  ✅ DataLoader imported")

    from ansible.vars.manager import VariableManager

    print("  ✅ VariableManager imported")

    from ansible.inventory.manager import InventoryManager

    print("  ✅ InventoryManager imported")

    from ansible import context

    print("  ✅ context imported")

    from ansible.module_utils.common.collections import ImmutableDict

    print("  ✅ ImmutableDict imported")

except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("Step 3: Initializing plugin loader...")
init_plugin_loader()
print("  ✅ Plugin loader initialized")

print("Step 4: Setting context...")
context.CLIARGS = ImmutableDict(
    {
        "connection": "local",
        "forks": 1,
        "verbosity": 0,
    }
)
print("  ✅ Context set")

print("Step 5: Creating DataLoader...")
loader = DataLoader()
print("  ✅ DataLoader created")

print("Step 6: Creating InventoryManager...")
inventory = InventoryManager(loader=loader, sources=["localhost,"])
print("  ✅ InventoryManager created")

print("Step 7: Creating VariableManager...")
variable_manager = VariableManager(loader=loader, inventory=inventory)
print("  ✅ VariableManager created")

print("Step 8: Creating TaskQueueManager...")
print("  📝 About to create TaskQueueManager...")


# Add thread monitoring
def monitor_threads():
    """Monitor threads during TQM creation."""
    while True:
        thread_count = threading.active_count()
        threads = [f"{t.name}({t.ident})" for t in threading.enumerate()]
        print(f"    🧵 {thread_count} threads: {threads}")
        time.sleep(0.5)


monitor_thread = threading.Thread(target=monitor_threads, daemon=True)
monitor_thread.start()

try:
    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        passwords={},
    )
    print("  ✅ TaskQueueManager created")

    print("Step 9: Testing TQM cleanup...")
    print("  📝 About to call tqm.cleanup()...")

    # Try cleanup in a separate thread with timeout
    cleanup_done = threading.Event()
    cleanup_error = []

    def do_cleanup():
        try:
            tqm.cleanup()
            cleanup_done.set()
            print("  ✅ Cleanup completed")
        except Exception as e:
            cleanup_error.append(e)
            cleanup_done.set()
            print(f"  ❌ Cleanup failed: {e}")

    cleanup_thread = threading.Thread(target=do_cleanup)
    cleanup_thread.start()

    # Wait for cleanup with timeout
    if cleanup_done.wait(timeout=10):
        if cleanup_error:
            print(f"  ❌ Cleanup failed: {cleanup_error[0]}")
        else:
            print("  ✅ Cleanup completed successfully")
    else:
        print("  ⏰ Cleanup timed out after 10 seconds")
        print("  🔍 This is where the hang occurs!")

        # Try to get thread info
        print("  📊 Thread status during hang:")
        for t in threading.enumerate():
            print(f"    - {t.name}: {t.is_alive()}")

except Exception as e:
    print(f"❌ TaskQueueManager creation failed: {e}")
    import traceback

    traceback.print_exc()

print("\n🏁 Debug complete")
signal.alarm(0)  # Cancel timeout
