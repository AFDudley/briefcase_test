"""
Ansible play execution utilities.

This module provides functions to create and execute Ansible plays.
"""

import os
import threading
import traceback
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from briefcase_ansible_test.utils.data_processing import build_ansible_play_dict




def load_play(play_source, variable_manager, loader, output_callback):
    """
    Load an Ansible play from source.

    Args:
        play_source: Play source dictionary
        variable_manager: Ansible VariableManager instance
        loader: Ansible DataLoader instance
        output_callback: Function to call with output messages

    Returns:
        Play instance or None if failed
    """
    output_callback("Loading play definition...\n")
    try:
        play = Play().load(
            play_source, variable_manager=variable_manager, loader=loader
        )
        output_callback("✅ Play loaded successfully\n")

        # Debug play details
        output_callback(f"Play hosts: {play.hosts}\n")
        tasks = play.tasks if hasattr(play, 'tasks') else []
        output_callback(f"Play tasks: {len(tasks) if tasks else 0}\n")
        for i, task_block in enumerate(tasks):
            output_callback(f"  Block {i}: {task_block}\n")
            if hasattr(task_block, "block"):
                for j, task in enumerate(task_block.block):
                    output_callback(f"    Task {j}: {task.name} - {task.action}\n")
        return play
    except Exception as e:
        output_callback(f"❌ Play load failed: {e}\n")
        output_callback(f"Traceback: {traceback.format_exc()}\n")
        return None


def execute_play_with_timeout(tqm, play, output_callback, timeout=10):
    """
    Execute an Ansible play with timeout protection.

    Args:
        tqm: TaskQueueManager instance
        play: Play instance
        output_callback: Function to call with output messages
        timeout: Timeout in seconds (default: 10)

    Returns:
        int: Result code from play execution
    """
    import multiprocessing

    # Check multiprocessing.Process before running
    print(f"iOS_DEBUG: multiprocessing.Process is: {multiprocessing.Process}")
    print(f"iOS_DEBUG: multiprocessing module: {multiprocessing}")

    # Log to system for xcrun debugging
    print(f"iOS_DEBUG: About to call tqm.run(), PID: {os.getpid()}")
    print(f"iOS_DEBUG: Current thread count: {threading.active_count()}")
    print(f"iOS_DEBUG: Threading module: {threading}")

    result = None
    exception = None

    def run_with_timeout():
        nonlocal result, exception
        try:
            print("iOS_DEBUG: Inside timeout thread, about to call tqm.run()")
            print(f"iOS_DEBUG: Play object: {play}")
            print(f"iOS_DEBUG: Play hosts: {play.hosts}")
            print(f"iOS_DEBUG: TQM object: {tqm}")

            # Debug TQM attributes
            if hasattr(tqm, "_workers"):
                print(f"iOS_DEBUG: TQM._workers: {tqm._workers}")
            if hasattr(tqm, "_forks"):
                print(f"iOS_DEBUG: TQM._forks: {tqm._forks}")
            if hasattr(tqm, "_final_q"):
                print(f"iOS_DEBUG: TQM._final_q type: {type(tqm._final_q)}")

            result = tqm.run(play)
            print(f"iOS_DEBUG: tqm.run() completed with result: {result}")
        except Exception as e:
            print(f"iOS_DEBUG: tqm.run() exception: {e}")
            exception = e

    timeout_thread = threading.Thread(target=run_with_timeout)
    timeout_thread.start()
    timeout_thread.join(timeout=timeout)

    if timeout_thread.is_alive():
        if output_callback:
            output_callback(f"⚠️ TQM.run() timed out after {timeout} seconds\n")
        return 1
    elif exception:
        raise exception
    else:
        if output_callback:
            output_callback(f"Playbook completed with result: {result}\n")
        return result or 0
