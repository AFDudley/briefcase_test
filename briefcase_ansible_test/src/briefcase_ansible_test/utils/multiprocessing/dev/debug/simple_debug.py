#!/usr/bin/env python3
"""
Simple step-by-step debugging of Ansible execution.
"""

import sys
import threading
import time

sys.path.insert(0, "src")

print("Step 1: Patching multiprocessing...")
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

print("Step 2: Testing our ThreadProcess run() fix...")
from briefcase_ansible_test.utils.multiprocessing.process import ThreadProcess


class TestProcess(ThreadProcess):
    def run(self):
        print("  🔹 TestProcess.run() called!")
        time.sleep(0.1)
        return "test result"


p = TestProcess()
p.start()
p.join()
print(f"  ✅ TestProcess completed with exit code: {p.exitcode}")

print("Step 3: Quick import check...")
try:
    from ansible.executor.task_queue_manager import TaskQueueManager

    print("  ✅ TaskQueueManager imported")
except Exception as e:
    print(f"  ❌ Import failed: {e}")
    sys.exit(1)

print("Step 4: Testing minimal Ansible setup...")
try:
    from ansible.plugins.loader import init_plugin_loader
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars.manager import VariableManager
    from ansible.inventory.manager import InventoryManager
    from ansible import context
    from ansible.module_utils.common.collections import ImmutableDict

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

    print("  ✅ Basic Ansible setup completed")

except Exception as e:
    print(f"  ❌ Ansible setup failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("Step 5: Creating TaskQueueManager...")
try:
    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        passwords={},
    )
    print("  ✅ TaskQueueManager created successfully")

    print("Step 6: Testing cleanup...")
    tqm.cleanup()
    print("  ✅ Cleanup completed")

except Exception as e:
    print(f"  ❌ TaskQueueManager failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("\n🎉 All basic steps completed successfully!")
print("The issue is specifically during tqm.run(play), not in setup.")

# Let's see if we can isolate the exact issue
print("\nStep 7: Testing a minimal play execution...")


def test_with_monitoring():
    """Test play execution with thread monitoring."""

    def monitor():
        for i in range(20):  # Monitor for 20 seconds
            time.sleep(1)
            thread_count = threading.active_count()
            threads = [t.name for t in threading.enumerate()]
            print(f"  Monitor: {thread_count} threads: {threads}")

    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()

    try:
        from ansible.playbook.play import Play

        play_source = {
            "name": "Monitor Test",
            "hosts": "localhost",
            "gather_facts": "no",
            "tasks": [{"name": "Simple debug", "debug": {"msg": "test"}}],
        }

        play = Play().load(
            play_source, variable_manager=variable_manager, loader=loader
        )
        print("  ✅ Play created")

        # Create fresh TQM
        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            passwords={},
        )
        print("  ✅ Fresh TaskQueueManager created")

        print("  🚀 Starting play execution (this is where it might hang)...")

        # Use a separate thread with timeout
        result_queue = []
        exception_queue = []

        def run_play():
            try:
                result = tqm.run(play)
                result_queue.append(result)
                print(f"  ✅ Play completed with result: {result}")
            except Exception as e:
                exception_queue.append(e)
                print(f"  ❌ Play failed: {e}")

        play_thread = threading.Thread(target=run_play)
        play_thread.start()

        # Wait for completion or timeout
        play_thread.join(timeout=10)

        if play_thread.is_alive():
            print("  ⏰ Play execution timed out after 10 seconds")
            print("  🔍 This confirms the hanging issue exists")
            return False
        elif result_queue:
            print(f"  🎉 Play completed successfully with result: {result_queue[0]}")
            return True
        elif exception_queue:
            print(f"  ❌ Play failed with exception: {exception_queue[0]}")
            return False
        else:
            print("  ❓ Play thread completed but no result")
            return False

    except Exception as e:
        print(f"  ❌ Error during play test: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        try:
            tqm.cleanup()
        except:
            pass


if test_with_monitoring():
    print("\n🎉 SUCCESS: The hanging issue has been resolved!")
else:
    print("\n🔍 ANALYSIS: The hanging issue still exists during play execution.")
    print("Our run() method fix is working, but there's another blocking operation.")
