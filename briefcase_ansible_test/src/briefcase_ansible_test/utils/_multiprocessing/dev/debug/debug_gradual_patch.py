#!/usr/bin/env python3
"""
Debug with gradual patching to find the issue.
"""

import sys
import threading
import time

sys.path.insert(0, "src")

print("🔍 Testing gradual patching...")

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

# Test if we can import our components without patching
print("Step 1: Importing our multiprocessing components...")
try:
    from briefcase_ansible_test.utils._multiprocessing.process import ThreadProcess
    from briefcase_ansible_test.utils._multiprocessing.queues import ProcessQueue
    from briefcase_ansible_test.utils._multiprocessing.context import get_context

    print("✅ Our components imported successfully")
except Exception as e:
    print(f"❌ Component import failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Test basic functionality
print("Step 2: Testing basic functionality...")


def test_func():
    return "working"


p = ThreadProcess(target=test_func)
p.start()
p.join()
print(f"✅ Basic functionality works (exit code: {p.exitcode})")

# Now try patching just the main multiprocessing module
print("Step 3: Patching just the main multiprocessing module...")
import briefcase_ansible_test.utils._multiprocessing as our_mp

original_mp = sys.modules.get("multiprocessing")
sys.modules["multiprocessing"] = our_mp
print("✅ Main multiprocessing module patched")

# Test import of a simple Ansible component
print("Step 4: Testing simple Ansible import...")
try:
    from ansible.module_utils.common.collections import ImmutableDict

    print("✅ ImmutableDict imported")

    test_dict = ImmutableDict({"test": "value"})
    print("✅ ImmutableDict works")
except Exception as e:
    print(f"❌ ImmutableDict failed: {e}")

# Try importing context
print("Step 5: Testing Ansible context import...")
try:
    from ansible import context

    print("✅ Ansible context imported")
except Exception as e:
    print(f"❌ Ansible context failed: {e}")
    import traceback

    traceback.print_exc()

# Try data loader
print("Step 6: Testing DataLoader import...")
try:
    from ansible.parsing.dataloader import DataLoader

    print("✅ DataLoader imported")

    loader = DataLoader()
    print("✅ DataLoader created")
except Exception as e:
    print(f"❌ DataLoader failed: {e}")
    import traceback

    traceback.print_exc()

# Try plugin loader
print("Step 7: Testing plugin loader...")
try:
    from ansible.plugins.loader import init_plugin_loader

    print("✅ init_plugin_loader imported")

    print("  📝 Calling init_plugin_loader()...")
    init_plugin_loader()
    print("✅ Plugin loader initialized")
except Exception as e:
    print(f"❌ Plugin loader failed: {e}")
    import traceback

    traceback.print_exc()

# The critical test - TaskQueueManager
print("Step 8: Testing TaskQueueManager import...")
try:
    print("  📝 Importing TaskQueueManager...")
    from ansible.executor.task_queue_manager import TaskQueueManager

    print("✅ TaskQueueManager imported successfully!")

    # Quick setup
    from ansible.vars.manager import VariableManager
    from ansible.inventory.manager import InventoryManager

    context.CLIARGS = ImmutableDict(
        {
            "connection": "local",
            "forks": 1,
            "verbosity": 0,
        }
    )

    inventory = InventoryManager(loader=loader, sources=["localhost,"])
    variable_manager = VariableManager(loader=loader, inventory=inventory)

    print("  📝 Creating TaskQueueManager...")
    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        passwords={},
    )
    print("✅ TaskQueueManager created!")

    tqm.cleanup()
    print("✅ Cleanup successful")

except Exception as e:
    print(f"❌ TaskQueueManager failed: {e}")
    import traceback

    traceback.print_exc()

# Restore original if needed
if original_mp:
    sys.modules["multiprocessing"] = original_mp

print("\n🏁 Gradual patching test complete")
