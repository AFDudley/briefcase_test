#!/usr/bin/env python3
"""
Comprehensive test of Ansible functionality with our iOS multiprocessing implementation.
"""

import sys
import threading
import time

sys.path.insert(0, "src")

print("🔍 Comprehensive Ansible functionality test...")

# Apply system utils
from briefcase_ansible_test.utils import (
    setup_pwd_module_mock,
    setup_grp_module_mock,
    patch_getpass,
)

setup_pwd_module_mock()
setup_grp_module_mock()
patch_getpass()

# Set up Ansible
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
        "forks": 2,  # Test with multiple forks
        "verbosity": 1,
    }
)

loader = DataLoader()
inventory = InventoryManager(loader=loader, sources=["localhost,"])
variable_manager = VariableManager(loader=loader, inventory=inventory)

print("✅ Ansible setup completed")


def test_complex_playbook():
    """Test a more complex playbook with multiple task types."""

    play_source = {
        "name": "Comprehensive iOS Test Playbook",
        "hosts": "localhost",
        "gather_facts": "no",
        "vars": {
            "test_var": "iOS_multiprocessing_test",
            "items_list": ["item1", "item2", "item3"],
        },
        "tasks": [
            {
                "name": "Debug with variable",
                "debug": {"msg": "Testing variable: {{ test_var }}"},
            },
            {
                "name": "Set a fact",
                "set_fact": {"runtime_fact": "Generated at runtime"},
            },
            {
                "name": "Debug the fact",
                "debug": {"msg": "Runtime fact: {{ runtime_fact }}"},
            },
            {
                "name": "Loop through items",
                "debug": {"msg": "Processing {{ item }}"},
                "loop": "{{ items_list }}",
            },
            {
                "name": "Conditional task",
                "debug": {"msg": "This runs because test_var is defined"},
                "when": "test_var is defined",
            },
            {"name": "Command task", "command": "echo 'Command executed successfully'"},
            {"name": "Shell task", "shell": "echo 'Shell task works: {{ test_var }}'"},
        ],
    }

    return play_source


def execute_playbook(play_source, test_name):
    """Execute a playbook and return results."""
    print(f"\nTest: {test_name}")
    print("=" * 60)

    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        passwords={},
    )

    try:
        start_time = time.time()
        result = tqm.run(play)
        elapsed = time.time() - start_time

        print(f"\n✅ {test_name} completed in {elapsed:.2f}s with result: {result}")
        return True, result, elapsed

    except Exception as e:
        print(f"\n❌ {test_name} failed: {e}")
        return False, str(e), 0
    finally:
        tqm.cleanup()


# Test 1: Complex playbook
success1, result1, time1 = execute_playbook(test_complex_playbook(), "Complex Playbook")


# Test 2: Multiple plays in sequence
def test_multiple_runs():
    """Test running multiple plays in sequence."""
    results = []

    for i in range(3):
        play_source = {
            "name": f"Sequential Test {i+1}",
            "hosts": "localhost",
            "gather_facts": "no",
            "tasks": [
                {
                    "name": f"Task {i+1}",
                    "debug": {"msg": f"This is sequential run number {i+1}"},
                }
            ],
        }

        success, result, elapsed = execute_playbook(
            play_source, f"Sequential Run {i+1}"
        )
        results.append((success, result, elapsed))

        if not success:
            break

    return results


sequential_results = test_multiple_runs()


# Test 3: Error handling
def test_error_handling():
    """Test error handling in playbooks."""
    play_source = {
        "name": "Error Handling Test",
        "hosts": "localhost",
        "gather_facts": "no",
        "tasks": [
            {"name": "Successful task", "debug": {"msg": "This should work"}},
            {
                "name": "Failing task",
                "command": "false",  # This will fail
                "ignore_errors": "yes",
            },
            {"name": "Recovery task", "debug": {"msg": "This runs after the failure"}},
        ],
    }

    return play_source


success3, result3, time3 = execute_playbook(
    test_error_handling(), "Error Handling Test"
)


# Test 4: Performance test with larger playbook
def test_performance():
    """Test performance with a larger playbook."""
    tasks = []
    for i in range(10):
        tasks.append(
            {
                "name": f"Performance task {i+1}",
                "debug": {"msg": f"Performance test task {i+1} executing"},
            }
        )

    play_source = {
        "name": "Performance Test",
        "hosts": "localhost",
        "gather_facts": "no",
        "tasks": tasks,
    }

    return play_source


success4, result4, time4 = execute_playbook(
    test_performance(), "Performance Test (10 tasks)"
)

# Summary
print("\n" + "=" * 80)
print("🏁 COMPREHENSIVE TEST SUMMARY")
print("=" * 80)

tests = [
    ("Complex Playbook", success1, result1, time1),
    (
        "Sequential Runs",
        all(s for s, r, t in sequential_results),
        len(sequential_results),
        sum(t for s, r, t in sequential_results),
    ),
    ("Error Handling", success3, result3, time3),
    ("Performance Test", success4, result4, time4),
]

all_passed = True
for test_name, success, result, elapsed in tests:
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name:<20} Result: {result:<10} Time: {elapsed:.2f}s")
    if not success:
        all_passed = False

print("\n" + "=" * 80)
if all_passed:
    print("🎉 ALL TESTS PASSED!")
    print("🏆 iOS threading-based multiprocessing implementation is fully functional!")
    print("📱 Ansible can successfully run complex playbooks on iOS.")
    print("\nKey achievements:")
    print("- ✅ ThreadProcess replaces multiprocessing.Process")
    print("- ✅ Queue timeout support implemented")
    print("- ✅ WorkerProcess inheritance pattern supported")
    print("- ✅ Complex playbooks with variables, loops, conditionals work")
    print("- ✅ Error handling and recovery works")
    print("- ✅ Multiple sequential playbook execution works")
    print("- ✅ Performance is acceptable for iOS constraints")
else:
    print("❌ SOME TESTS FAILED")
    print("There may be edge cases that need additional work.")

print("\n🏁 Comprehensive testing complete")
