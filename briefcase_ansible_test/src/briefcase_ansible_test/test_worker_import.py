"""
Test importing Ansible's WorkerProcess to debug the hang
"""


def test_worker_import(ui_updater):
    """Test if we can import WorkerProcess without hanging"""
    ui_updater.add_text_to_output("Testing WorkerProcess import...\n")

    import sys

    ui_updater.add_text_to_output(
        f"multiprocessing in sys.modules: {'multiprocessing' in sys.modules}\n"
    )
    ui_updater.add_text_to_output(
        f"multiprocessing.queues in sys.modules: {'multiprocessing.queues' in sys.modules}\n"
    )

    # Try to import multiprocessing.queues.Queue directly
    ui_updater.add_text_to_output("\nTrying to import from multiprocessing.queues...\n")
    try:
        from multiprocessing.queues import Queue

        ui_updater.add_text_to_output(f"✅ Queue imported: {Queue}\n")
        ui_updater.add_text_to_output(f"Queue.__module__: {Queue.__module__}\n")
        ui_updater.add_text_to_output(f"Queue.__bases__: {Queue.__bases__}\n")
    except Exception as e:
        ui_updater.add_text_to_output(f"❌ Failed to import Queue: {e}\n")
        import traceback

        ui_updater.add_text_to_output(f"Traceback: {traceback.format_exc()}\n")

    # Try to create a subclass like WorkerQueue does
    ui_updater.add_text_to_output("\nTrying to subclass Queue...\n")
    try:
        from multiprocessing.queues import Queue

        class TestQueue(Queue):
            def get(self, *args, **kwargs):
                result = super(TestQueue, self).get(*args, **kwargs)
                return result

        ui_updater.add_text_to_output("✅ Successfully created Queue subclass\n")

        # Try to instantiate it
        tq = TestQueue()
        ui_updater.add_text_to_output(f"✅ Successfully instantiated TestQueue: {tq}\n")

    except Exception as e:
        ui_updater.add_text_to_output(f"❌ Failed to subclass Queue: {e}\n")
        import traceback

        ui_updater.add_text_to_output(f"Traceback: {traceback.format_exc()}\n")

    # Test ansible.utils.multiprocessing first
    ui_updater.add_text_to_output(
        "\nTrying to import ansible.utils.multiprocessing...\n"
    )
    try:
        import ansible.utils.multiprocessing

        ui_updater.add_text_to_output(
            f"✅ ansible.utils.multiprocessing imported: {ansible.utils.multiprocessing}\n"
        )
        ui_updater.add_text_to_output(
            f"context attribute: {getattr(ansible.utils.multiprocessing, 'context', 'NOT FOUND')}\n"
        )

        # Try to access multiprocessing_context
        from ansible.utils.multiprocessing import context as multiprocessing_context

        ui_updater.add_text_to_output(
            f"✅ multiprocessing_context imported: {multiprocessing_context}\n"
        )
        ui_updater.add_text_to_output(
            f"multiprocessing_context.Process: {getattr(multiprocessing_context, 'Process', 'NOT FOUND')}\n"
        )
    except Exception as e:
        ui_updater.add_text_to_output(
            f"❌ Failed to import ansible.utils.multiprocessing: {e}\n"
        )
        import traceback

        ui_updater.add_text_to_output(f"Traceback: {traceback.format_exc()}\n")

    # Now try the actual WorkerProcess import
    ui_updater.add_text_to_output("\nTrying to import WorkerProcess...\n")
    try:
        import ansible.executor.process

        ui_updater.add_text_to_output("✅ ansible.executor.process imported\n")

        # Try importing step by step
        ui_updater.add_text_to_output("Importing worker module components...\n")

        # These are the imports from worker.py
        ui_updater.add_text_to_output("  - multiprocessing.queues.Queue... ")
        from multiprocessing.queues import Queue

        ui_updater.add_text_to_output("✅\n")

        ui_updater.add_text_to_output("  - ansible.errors... ")
        from ansible.errors import AnsibleConnectionFailure, AnsibleError

        ui_updater.add_text_to_output("✅\n")

        ui_updater.add_text_to_output("  - ansible.executor.task_executor... ")
        from ansible.executor.task_executor import TaskExecutor

        ui_updater.add_text_to_output("✅\n")

        ui_updater.add_text_to_output(
            "  - ansible.module_utils.common.text.converters... "
        )
        from ansible.module_utils.common.text.converters import to_text

        ui_updater.add_text_to_output("✅\n")

        ui_updater.add_text_to_output("  - ansible.utils.display... ")
        from ansible.utils.display import Display

        ui_updater.add_text_to_output("✅\n")

        ui_updater.add_text_to_output("  - ansible.utils.multiprocessing context... ")
        from ansible.utils.multiprocessing import context as multiprocessing_context

        ui_updater.add_text_to_output("✅\n")

        ui_updater.add_text_to_output("\nNow importing WorkerProcess itself...\n")
        from ansible.executor.process.worker import WorkerProcess

        ui_updater.add_text_to_output(f"✅ WorkerProcess imported: {WorkerProcess}\n")
        ui_updater.add_text_to_output(
            f"WorkerProcess.__bases__: {WorkerProcess.__bases__}\n"
        )

    except Exception as e:
        ui_updater.add_text_to_output(f"❌ Failed to import WorkerProcess: {e}\n")
        import traceback

        ui_updater.add_text_to_output(f"Traceback: {traceback.format_exc()}\n")

    ui_updater.add_text_to_output("\nWorker import test completed\n")
