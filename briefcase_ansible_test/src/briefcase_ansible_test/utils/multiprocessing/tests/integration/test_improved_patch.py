#!/usr/bin/env python3
"""
Test the improved patch function with auto-patching enabled.
"""

import sys
import threading
import time

sys.path.insert(0, "src")

print("🔍 Testing improved patch function with auto-patching...")

# Apply system utils
from briefcase_ansible_test.utils import (
    setup_pwd_module_mock,
    setup_grp_module_mock,
    patch_getpass,
)

setup_pwd_module_mock()
setup_grp_module_mock()
patch_getpass()
print("✅ System utils applied")

# Import our multiprocessing (should auto-patch)
print("Step 1: Importing multiprocessing with auto-patch...")
from briefcase_ansible_test.utils.multiprocessing import _patch_system_modules

print("✅ Auto-patching applied")

# Test basic functionality
print("Step 2: Testing basic functionality...")
from briefcase_ansible_test.utils.multiprocessing.process import ThreadProcess


def test_func():
    return "working"


p = ThreadProcess(target=test_func)
p.start()
p.join()
print(f"✅ Basic functionality works (exit code: {p.exitcode})")

# Test Ansible import and setup
print("Step 3: Testing Ansible import and setup...")
try:
    from ansible.executor.task_queue_manager import TaskQueueManager
    from ansible.plugins.loader import init_plugin_loader
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars.manager import VariableManager
    from ansible.inventory.manager import InventoryManager
    from ansible import context
    from ansible.module_utils.common.collections import ImmutableDict

    print("✅ Ansible modules imported successfully")

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

    print("✅ Ansible setup completed")

    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        passwords={},
    )
    print("✅ TaskQueueManager created")

    tqm.cleanup()
    print("✅ Cleanup successful")

except Exception as e:
    print(f"❌ Ansible failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("Step 4: Testing play execution...")


def test_play_execution():
    """Test actual play execution."""
    from ansible.playbook.play import Play

    # Create a simple play
    play_source = {
        "name": "Improved Patch Test",
        "hosts": "localhost",
        "gather_facts": "no",
        "tasks": [
            {"name": "Debug message", "debug": {"msg": "Hello from improved patch!"}}
        ],
    }

    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

    # Create new TQM for execution
    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        passwords={},
    )

    # Execute with monitoring
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

            if elapsed > 20:  # 20 second timeout
                print("    ⏰ TIMEOUT - execution hung")
                break

            if execution_done.wait(timeout=2):
                break

    def execute():
        try:
            print("  📝 Executing play...")
            result = tqm.run(play)
            execution_result.append(result)
            execution_done.set()
            print(f"  ✅ Play completed with result: {result}")
        except Exception as e:
            execution_error.append(e)
            execution_done.set()
            print(f"  ❌ Play failed: {e}")
            import traceback

            traceback.print_exc()

    monitor_thread = threading.Thread(target=monitor, daemon=True)
    execution_thread = threading.Thread(target=execute, name="PlayExecution")

    monitor_thread.start()
    execution_thread.start()

    execution_thread.join(timeout=25)

    # Cleanup
    try:
        tqm.cleanup()
    except:
        pass

    if execution_thread.is_alive():
        return False, "hung"
    elif execution_result:
        return True, execution_result[0]
    elif execution_error:
        return False, execution_error[0]
    else:
        return False, "unknown"


success, result = test_play_execution()

if success:
    print(f"\n🎉 SUCCESS: Play executed successfully with result: {result}")
    print("The improved patch function has resolved the hanging issue!")
else:
    print(f"\n❌ FAILURE: Play execution failed/hung: {result}")
    print("The hanging issue persists.")

print("\n🏁 Improved patch test complete")
