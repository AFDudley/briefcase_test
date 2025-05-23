#!/usr/bin/env python3
"""
Debug what multiprocessing operations Ansible is actually using.
"""

import sys
import threading
import time

sys.path.insert(0, "src")

# First, let's instrument our multiprocessing module to see what's being called
print("🔍 Setting up multiprocessing instrumentation...")

# Before patching, let's add some debugging to our implementation
original_patch = None


def instrument_multiprocessing():
    """Add debugging to our multiprocessing implementation."""

    # Instrument ThreadProcess
    from briefcase_ansible_test.utils.multiprocessing.process import ThreadProcess

    original_init = ThreadProcess.__init__
    original_start = ThreadProcess.start
    original_join = ThreadProcess.join

    def debug_init(
        self, group=None, target=None, name=None, args=(), kwargs={}, daemon=None
    ):
        print(f"  🔹 ThreadProcess.__init__(target={target}, name={name}, args={args})")
        return original_init(self, group, target, name, args, kwargs, daemon)

    def debug_start(self):
        print(f"  🔹 ThreadProcess.start() - {self.name}")
        return original_start(self)

    def debug_join(self, timeout=None):
        print(f"  🔹 ThreadProcess.join(timeout={timeout}) - {self.name}")
        result = original_join(self, timeout)
        print(f"  🔹 ThreadProcess.join() completed - {self.name}")
        return result

    ThreadProcess.__init__ = debug_init
    ThreadProcess.start = debug_start
    ThreadProcess.join = debug_join

    # Instrument queues
    from briefcase_ansible_test.utils.multiprocessing import queues

    original_queue_init = queues.ProcessQueue.__init__

    def debug_queue_init(self, maxsize=0):
        print(f"  🔹 ProcessQueue.__init__(maxsize={maxsize})")
        return original_queue_init(self, maxsize)

    queues.ProcessQueue.__init__ = debug_queue_init


print("Step 1: Applying instrumented patches...")
from briefcase_ansible_test.utils.multiprocessing import _patch_system_modules

# Add instrumentation before patching
instrument_multiprocessing()

_patch_system_modules()

from briefcase_ansible_test.utils.system_utils import (
    setup_pwd_module_mock,
    setup_grp_module_mock,
    patch_getpass,
)

setup_pwd_module_mock()
setup_grp_module_mock()
patch_getpass()
print("✅ Instrumented patches applied")

print("Step 2: Testing basic multiprocessing operations...")

# Test our instrumented ThreadProcess
from briefcase_ansible_test.utils.multiprocessing.process import ThreadProcess


def test_function():
    print("  🔸 test_function running")
    return "test_result"


p = ThreadProcess(target=test_function, name="TestProcess")
p.start()
p.join()
print(f"✅ Basic ThreadProcess test completed (exit code: {p.exitcode})")

print("Step 3: Minimal Ansible import test...")
try:
    # Import TaskQueueManager slowly and see what multiprocessing calls it makes
    print("  📝 Importing TaskQueueManager...")
    from ansible.executor.task_queue_manager import TaskQueueManager

    print("  ✅ TaskQueueManager imported")

    print("  📝 Importing supporting modules...")
    from ansible.plugins.loader import init_plugin_loader
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars.manager import VariableManager
    from ansible.inventory.manager import InventoryManager
    from ansible import context
    from ansible.module_utils.common.collections import ImmutableDict

    print("  ✅ Supporting modules imported")

except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("Step 4: Minimal Ansible setup with monitoring...")
try:
    print("  📝 Initializing plugin loader...")
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

except Exception as e:
    print(f"❌ Ansible setup failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("Step 5: Creating TaskQueueManager with full monitoring...")


def create_tqm_with_timeout():
    """Create TQM in a separate thread with timeout."""
    tqm_result = []
    tqm_error = []
    tqm_done = threading.Event()

    def create_tqm():
        try:
            print("  📝 Calling TaskQueueManager constructor...")
            tqm = TaskQueueManager(
                inventory=inventory,
                variable_manager=variable_manager,
                loader=loader,
                passwords={},
            )
            tqm_result.append(tqm)
            print("  ✅ TaskQueueManager created successfully")
            tqm_done.set()
        except Exception as e:
            tqm_error.append(e)
            print(f"  ❌ TaskQueueManager creation failed: {e}")
            import traceback

            traceback.print_exc()
            tqm_done.set()

    # Monitor threads during TQM creation
    def monitor():
        start_time = time.time()
        while not tqm_done.is_set():
            elapsed = time.time() - start_time
            thread_count = threading.active_count()
            threads = [f"{t.name}" for t in threading.enumerate()]
            print(f"    [{elapsed:.1f}s] 🧵 {thread_count} threads: {threads}")
            time.sleep(0.5)

    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()

    creation_thread = threading.Thread(target=create_tqm, name="TQMCreation")
    creation_thread.start()

    # Wait for completion with timeout
    if tqm_done.wait(timeout=15):
        if tqm_result:
            return tqm_result[0]
        elif tqm_error:
            raise tqm_error[0]
        else:
            raise Exception("TQM creation completed but no result")
    else:
        print("  ⏰ TaskQueueManager creation timed out after 15 seconds")
        print("  🔍 This indicates a hang during TQM construction")
        return None


tqm = create_tqm_with_timeout()

if tqm:
    print("🎉 SUCCESS: TaskQueueManager created without hanging")
    try:
        tqm.cleanup()
        print("✅ Cleanup completed")
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
else:
    print("❌ FAILED: TaskQueueManager creation hung")

print("\n🏁 Multiprocessing usage analysis complete")
