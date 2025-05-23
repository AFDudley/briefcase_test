#!/usr/bin/env python3
"""
Final test of Ansible play execution with all fixes applied.
"""

import sys
import threading
import time

sys.path.insert(0, "src")

print("🔍 Final test of Ansible play execution...")

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

# Our multiprocessing should be auto-patched now
print("Step 1: Testing multiprocessing auto-patch...")
try:
    import multiprocessing

    p = multiprocessing.Process(target=lambda: None)
    print(f"✅ multiprocessing.Process type: {type(p)}")

    # Quick verification our Process works
    def test_func():
        return "working"

    p = multiprocessing.Process(target=test_func)
    p.start()
    p.join()
    print(f"✅ Basic multiprocessing test (exit code: {p.exitcode})")

except Exception as e:
    print(f"❌ Multiprocessing test failed: {e}")
    sys.exit(1)

print("Step 2: Setting up Ansible...")
try:
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

    print("✅ Ansible setup completed")

except Exception as e:
    print(f"❌ Ansible setup failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("Step 3: Creating and executing play...")


def execute_ansible_play():
    """Execute a complete Ansible play."""

    # Create a simple play
    play_source = {
        "name": "Final Integration Test",
        "hosts": "localhost",
        "gather_facts": "no",
        "tasks": [
            {
                "name": "Debug message task",
                "debug": {"msg": "Hello from iOS threading-based multiprocessing!"},
            },
            {
                "name": "Another debug task",
                "debug": {"msg": "Task 2 executed successfully"},
            },
        ],
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

            if elapsed > 30:  # 30 second timeout
                print("    ⏰ TIMEOUT - execution appears hung")
                break

            if execution_done.wait(timeout=3):
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

    execution_thread.join(timeout=35)

    # Cleanup
    try:
        tqm.cleanup()
        print("✅ TaskQueueManager cleanup completed")
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")

    if execution_thread.is_alive():
        return False, "hung"
    elif execution_result:
        return True, execution_result[0]
    elif execution_error:
        return False, execution_error[0]
    else:
        return False, "unknown"


success, result = execute_ansible_play()

if success:
    print(f"\n🎉 SUCCESS: Ansible play executed successfully!")
    print(f"Play result: {result}")
    print("\n🏆 iOS threading-based multiprocessing implementation is working!")
    print("Ansible can now run tasks on iOS using our ThreadProcess implementation.")
else:
    print(f"\n❌ FAILURE: Play execution failed/hung: {result}")
    print("There may still be issues to resolve.")

print("\n🏁 Final integration test complete")
