#!/usr/bin/env python3
"""
Debug TaskQueueManager cleanup hanging issue.
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


# Timeout handler
def timeout_handler(signum, frame):
    print("\n⏰ TIMEOUT during cleanup!")
    print("Active threads:")
    for t in threading.enumerate():
        print(f"  - {t.name}: {t.is_alive()}")
    sys.exit(1)


signal.signal(signal.SIGALRM, timeout_handler)

try:
    from ansible.plugins.loader import init_plugin_loader
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars.manager import VariableManager
    from ansible.inventory.manager import InventoryManager
    from ansible.executor.task_queue_manager import TaskQueueManager
    from ansible import context
    from ansible.module_utils.common.collections import ImmutableDict

    print("Setting up Ansible...")
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

    print("Creating TaskQueueManager...")
    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        passwords={},
    )
    print("✅ TaskQueueManager created")

    # Check what's in the TaskQueueManager that might cause hanging
    print(f"TQM attributes: {[attr for attr in dir(tqm) if not attr.startswith('_')]}")

    # Check for any background processes or threads
    print(f"Threads before cleanup: {threading.active_count()}")
    for t in threading.enumerate():
        print(f"  - {t.name}: {t.is_alive()}")

    print("Starting cleanup with 10s timeout...")
    signal.alarm(10)

    # Try to cleanup
    tqm.cleanup()

    signal.alarm(0)
    print("✅ Cleanup completed successfully!")

    print(f"Threads after cleanup: {threading.active_count()}")
    for t in threading.enumerate():
        print(f"  - {t.name}: {t.is_alive()}")

except Exception as e:
    signal.alarm(0)
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()

print("Test completed")
