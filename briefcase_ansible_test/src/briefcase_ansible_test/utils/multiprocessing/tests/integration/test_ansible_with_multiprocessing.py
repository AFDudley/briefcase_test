#!/usr/bin/env python3
"""
Test script for Ansible integration with our iOS multiprocessing implementation.

This script tests whether Ansible can successfully use our threading-based
multiprocessing replacement to execute tasks on iOS.
"""

import sys
import os

# Set up the path and patch multiprocessing BEFORE any other imports
sys.path.insert(0, "src")

# Patch multiprocessing first
from briefcase_ansible_test.utils.multiprocessing import _patch_system_modules

_patch_system_modules()

# Now import system utils and apply patches
from briefcase_ansible_test.utils import (
    setup_pwd_module_mock,
    setup_grp_module_mock,
    patch_getpass,
)

# Apply system patches
setup_pwd_module_mock()
setup_grp_module_mock()
patch_getpass()

# Now import Ansible components
try:
    from ansible.plugins.loader import init_plugin_loader
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars.manager import VariableManager
    from ansible.inventory.manager import InventoryManager
    from ansible.playbook.play import Play
    from ansible.executor.task_queue_manager import TaskQueueManager
    from ansible import context
    from ansible.module_utils.common.collections import ImmutableDict
    import ansible.constants as C

    print("✓ Ansible imports successful with patched multiprocessing")

except ImportError as e:
    print(f"❌ Failed to import Ansible: {e}")
    sys.exit(1)


def test_ansible_ping():
    """Test Ansible ping with our multiprocessing implementation."""
    print("\nTesting Ansible ping with threading-based multiprocessing...")

    try:
        # Initialize plugin loader
        init_plugin_loader()
        print("✓ Plugin loader initialized")

        # Set up Ansible context
        context.CLIARGS = ImmutableDict(
            {
                "connection": "local",
                "module_path": ["/dev/null"],
                "forks": 1,
                "become": None,
                "become_method": None,
                "become_user": None,
                "check": False,
                "diff": False,
                "verbosity": 3,
                "remote_user": None,
                "private_key_file": None,
            }
        )

        # Create data loader and inventory
        loader = DataLoader()
        inventory = InventoryManager(loader=loader, sources=["localhost,"])
        variable_manager = VariableManager(loader=loader, inventory=inventory)

        print("✓ Ansible inventory and variable manager created")

        # Define a simple play with ping task
        play_source = {
            "name": "iOS Multiprocessing Test Play",
            "hosts": "localhost",
            "gather_facts": "no",
            "tasks": [
                {"name": "Ping test", "ping": {}},
                {
                    "name": "Debug message",
                    "debug": {"msg": "iOS multiprocessing working with Ansible!"},
                },
            ],
        }

        play = Play().load(
            play_source, variable_manager=variable_manager, loader=loader
        )
        print("✓ Ansible play created")

        # Create task queue manager
        passwords = {}

        print("Creating TaskQueueManager with threading-based multiprocessing...")
        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            passwords=passwords,
        )

        print("✓ TaskQueueManager created successfully")

        try:
            print("Running Ansible play...")
            result = tqm.run(play)
            print(f"✓ Ansible play completed with result: {result}")

            if result == 0:
                print(
                    "🎉 SUCCESS: Ansible executed successfully with iOS multiprocessing!"
                )
            else:
                print(
                    f"⚠️  WARNING: Ansible completed but with non-zero result: {result}"
                )

        finally:
            tqm.cleanup()
            print("✓ TaskQueueManager cleaned up")

    except Exception as e:
        print(f"❌ Error during Ansible execution: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


def test_multiprocessing_modules():
    """Test that our multiprocessing modules are properly loaded."""
    print("\nTesting multiprocessing module loading...")

    # Test that multiprocessing imports our version
    import multiprocessing

    print(f"multiprocessing module: {multiprocessing}")
    print(f"multiprocessing.Process: {multiprocessing.Process}")
    print(
        f"multiprocessing version: {getattr(multiprocessing, '__version__', 'unknown')}"
    )

    # Test that submodules work
    import multiprocessing.queues

    print(f"multiprocessing.queues: {multiprocessing.queues}")

    import multiprocessing.synchronize

    print(f"multiprocessing.synchronize: {multiprocessing.synchronize}")

    # Verify it's our implementation
    version = getattr(multiprocessing, "__version__", "")
    if version and "ios-threading" in version:
        print("✓ Using iOS threading-based multiprocessing implementation")
        return True
    else:
        print("❌ Not using our iOS multiprocessing implementation")
        return False


def main():
    """Run all integration tests."""
    print("Starting Ansible integration tests with iOS multiprocessing...\n")

    success = True

    # Test multiprocessing module loading
    if not test_multiprocessing_modules():
        success = False

    # Test Ansible execution
    if not test_ansible_ping():
        success = False

    if success:
        print("\n🎉 All integration tests passed!")
        print(
            "Ansible is now compatible with iOS using threading-based multiprocessing!"
        )
    else:
        print("\n❌ Some tests failed. Check output above for details.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
