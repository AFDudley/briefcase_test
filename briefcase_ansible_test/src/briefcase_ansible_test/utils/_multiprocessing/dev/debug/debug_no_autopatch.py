#!/usr/bin/env python3
"""
Debug without auto-patching to isolate the issue.
"""

import sys
import threading
import time

sys.path.insert(0, "src")

print("🔍 Testing without auto-patching...")

# Apply system utils first
from briefcase_ansible_test.utils.system_utils import (
    setup_pwd_module_mock,
    setup_grp_module_mock,
    patch_getpass,
)

setup_pwd_module_mock()
setup_grp_module_mock()
patch_getpass()
print("✅ System utils applied")

# Test basic imports without our multiprocessing
print("Step 1: Testing Ansible imports without our multiprocessing...")
try:
    from ansible.executor.task_queue_manager import TaskQueueManager

    print("  ✅ TaskQueueManager imported (using system multiprocessing)")

    from ansible.plugins.loader import init_plugin_loader
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars.manager import VariableManager
    from ansible.inventory.manager import InventoryManager
    from ansible import context
    from ansible.module_utils.common.collections import ImmutableDict

    print("  ✅ All Ansible modules imported successfully")

except Exception as e:
    print(f"  ❌ Ansible import failed: {e}")
    import traceback

    traceback.print_exc()

print("Step 2: Testing basic Ansible setup...")
try:
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

    print("  ✅ Basic Ansible setup successful")

except Exception as e:
    print(f"  ❌ Ansible setup failed: {e}")
    import traceback

    traceback.print_exc()

print("Step 3: Testing TaskQueueManager creation...")
try:
    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        passwords={},
    )
    print("  ✅ TaskQueueManager created (this should fail or hang on iOS)")

    tqm.cleanup()
    print("  ✅ Cleanup successful")

except Exception as e:
    print(f"  ❌ TaskQueueManager failed (expected on iOS): {e}")

print("\nStep 4: Now testing with our multiprocessing...")

# Import our multiprocessing but don't auto-patch
print("  📝 Importing our multiprocessing components...")
import importlib

multiprocessing_module = importlib.import_module(
    "briefcase_ansible_test.utils._multiprocessing"
)

# Manual patch just multiprocessing
original_multiprocessing = sys.modules.get("multiprocessing")
sys.modules["multiprocessing"] = multiprocessing_module
print("  ✅ Manually patched multiprocessing")

try:
    # Re-import Ansible components to pick up our multiprocessing
    print("  📝 Re-importing TaskQueueManager with our multiprocessing...")

    # Need to reload modules to pick up new multiprocessing
    importlib.reload(sys.modules["ansible.executor.task_queue_manager"])

    from ansible.executor.task_queue_manager import TaskQueueManager as NewTQM

    print("  ✅ TaskQueueManager re-imported with our multiprocessing")

    # Test creation
    new_tqm = NewTQM(
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        passwords={},
    )
    print("  ✅ TaskQueueManager created with our multiprocessing!")

    new_tqm.cleanup()
    print("  ✅ Cleanup successful")

except Exception as e:
    print(f"  ❌ Our multiprocessing failed: {e}")
    import traceback

    traceback.print_exc()

# Restore original
if original_multiprocessing:
    sys.modules["multiprocessing"] = original_multiprocessing

print("\n🏁 Auto-patch debugging complete")
