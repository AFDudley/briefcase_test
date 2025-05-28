#!/usr/bin/env python3
"""
Test Ansible execution with our fixed multiprocessing implementation.
"""

import sys
import time
import signal

sys.path.insert(0, "src")

# Patch multiprocessing first
from briefcase_ansible_test.utils.multiprocessing import _patch_system_modules

_patch_system_modules()

from briefcase_ansible_test.utils import (
    setup_pwd_module_mock,
    setup_grp_module_mock,
    patch_getpass,
)

setup_pwd_module_mock()
setup_grp_module_mock()
patch_getpass()


def timeout_handler(signum, frame):
    print("\n⏰ Timeout reached - this indicates the fix may need more work")
    sys.exit(1)


# Set timeout
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(15)  # 15 second timeout

try:
    print("🔧 Testing Ansible with fixed multiprocessing...")

    from ansible.plugins.loader import init_plugin_loader
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars.manager import VariableManager
    from ansible.inventory.manager import InventoryManager
    from ansible.playbook.play import Play
    from ansible.executor.task_queue_manager import TaskQueueManager
    from ansible import context
    from ansible.module_utils.common.collections import ImmutableDict

    print("✅ Ansible imports successful")

    init_plugin_loader()
    print("✅ Plugin loader initialized")

    context.CLIARGS = ImmutableDict(
        {
            "connection": "local",
            "forks": 1,
            "become": None,
            "become_method": None,
            "become_user": None,
            "check": False,
            "diff": False,
            "verbosity": 1,
        }
    )

    loader = DataLoader()
    inventory = InventoryManager(loader=loader, sources=["localhost,"])
    variable_manager = VariableManager(loader=loader, inventory=inventory)

    print("✅ Ansible components created")

    # Simple play with debug task
    play_source = {
        "name": "Fixed iOS Test",
        "hosts": "localhost",
        "gather_facts": "no",
        "tasks": [
            {
                "name": "Test task",
                "debug": {"msg": "Success! iOS multiprocessing working!"},
            }
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

    print("🚀 Running play with fixed multiprocessing...")
    result = tqm.run(play)

    signal.alarm(0)  # Cancel timeout
    print(f"✅ Play completed with result: {result}")

    tqm.cleanup()
    print("✅ Cleanup completed")

    if result == 0:
        print("\n🎉 SUCCESS: Ansible task execution works with iOS multiprocessing!")
        print("The hanging issue has been resolved!")
    else:
        print(f"\n⚠️ Play completed but with result: {result}")

except Exception as e:
    signal.alarm(0)
    print(f"\n❌ Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
