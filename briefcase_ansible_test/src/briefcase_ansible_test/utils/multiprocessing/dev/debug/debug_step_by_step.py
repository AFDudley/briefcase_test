#!/usr/bin/env python3
"""
Step by step debugging to find exactly where hanging occurs.
"""

import sys
import threading
import time
import signal

sys.path.insert(0, "src")

# Patch multiprocessing
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


def timeout_handler(signum, frame):
    print(f"\n⏰ TIMEOUT in step: {current_step}")
    print("Active threads:")
    for t in threading.enumerate():
        print(f"  - {t.name}: {t.is_alive()}")
    sys.exit(1)


signal.signal(signal.SIGALRM, timeout_handler)
current_step = "initialization"

try:
    print("🔧 Step-by-step Ansible debugging")

    # Setup
    current_step = "imports"
    from ansible.plugins.loader import init_plugin_loader
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars.manager import VariableManager
    from ansible.inventory.manager import InventoryManager
    from ansible.playbook.play import Play
    from ansible.executor.task_queue_manager import TaskQueueManager
    from ansible import context
    from ansible.module_utils.common.collections import ImmutableDict

    print("✅ Imports completed")

    current_step = "plugin_loader"
    signal.alarm(5)
    init_plugin_loader()
    signal.alarm(0)
    print("✅ Plugin loader initialized")

    current_step = "context"
    context.CLIARGS = ImmutableDict(
        {
            "connection": "local",
            "forks": 1,
            "verbosity": 0,
        }
    )
    print("✅ Context set")

    current_step = "ansible_components"
    loader = DataLoader()
    inventory = InventoryManager(loader=loader, sources=["localhost,"])
    variable_manager = VariableManager(loader=loader, inventory=inventory)
    print("✅ Ansible components created")

    current_step = "play_creation"
    play_source = {
        "name": "Debug Test",
        "hosts": "localhost",
        "gather_facts": "no",
        "tasks": [{"name": "Debug task", "debug": {"msg": "test"}}],
    }
    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)
    print("✅ Play created")

    current_step = "tqm_creation"
    signal.alarm(5)
    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        passwords={},
    )
    signal.alarm(0)
    print("✅ TaskQueueManager created")

    # Now test different operations
    current_step = "tqm_run_start"
    print("🚀 Testing tqm.run() - this might hang...")

    # Create a thread to run the play with timeout
    result_holder = [None]
    exception_holder = [None]

    def run_play():
        try:
            result = tqm.run(play)
            result_holder[0] = result
        except Exception as e:
            exception_holder[0] = e

    play_thread = threading.Thread(target=run_play, name="PlayThread")
    play_thread.start()

    # Monitor for 15 seconds
    for i in range(15):
        time.sleep(1)
        if not play_thread.is_alive():
            break
        print(f"  Play thread still running... ({i+1}s)")

        # Print active threads
        threads = threading.enumerate()
        if len(threads) > 2:  # More than main + play thread
            print(f"    Active threads: {[t.name for t in threads]}")

    if play_thread.is_alive():
        print("❌ Play execution hung after 15 seconds")
        current_step = "hung_in_play_execution"

        # Let's see what threads are active
        print("Final thread state:")
        for t in threading.enumerate():
            print(f"  - {t.name}: alive={t.is_alive()}, daemon={t.daemon}")

        # Try to get a stack trace of the play thread
        import faulthandler

        print("\nStack trace:")
        faulthandler.dump_traceback()

    else:
        if exception_holder[0]:
            print(f"❌ Play execution failed: {exception_holder[0]}")
        else:
            print(f"✅ Play execution completed with result: {result_holder[0]}")

    current_step = "cleanup"
    signal.alarm(5)
    tqm.cleanup()
    signal.alarm(0)
    print("✅ Cleanup completed")

except Exception as e:
    signal.alarm(0)
    print(f"❌ Error in step '{current_step}': {e}")
    import traceback

    traceback.print_exc()

finally:
    signal.alarm(0)
    print("Debug completed")
