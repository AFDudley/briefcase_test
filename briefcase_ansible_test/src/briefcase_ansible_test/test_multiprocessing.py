"""
Test our multiprocessing implementation directly
"""


def test_multiprocessing(ui_updater):
    """Test if our multiprocessing implementation works on iOS"""
    ui_updater.add_text_to_output("Testing multiprocessing implementation...\n")

    import multiprocessing
    import time

    ui_updater.add_text_to_output(f"multiprocessing module: {multiprocessing}\n")
    ui_updater.add_text_to_output(
        f"multiprocessing.Process: {multiprocessing.Process}\n"
    )

    def worker_function(name):
        print(f"iOS_DEBUG: Worker {name} started")
        time.sleep(0.1)
        print(f"iOS_DEBUG: Worker {name} finished")
        return f"Result from {name}"

    # Test 1: Create and start a Process
    ui_updater.add_text_to_output("\nTest 1: Basic Process creation\n")
    try:
        p = multiprocessing.Process(target=worker_function, args=("test1",))
        ui_updater.add_text_to_output(f"Process created: {p}\n")
        p.start()
        ui_updater.add_text_to_output("Process started\n")
        p.join(timeout=2)
        ui_updater.add_text_to_output(f"Process finished, exitcode: {p.exitcode}\n")
    except Exception as e:
        ui_updater.add_text_to_output(f"ERROR: {e}\n")
        import traceback

        ui_updater.add_text_to_output(f"Traceback: {traceback.format_exc()}\n")

    # Test 2: Test subclassing Process (like Ansible's WorkerProcess does)
    ui_updater.add_text_to_output("\nTest 2: Subclassed Process\n")

    class TestWorkerProcess(multiprocessing.Process):
        def __init__(self, name):
            super().__init__()
            self.worker_name = name

        def run(self):
            print(f"iOS_DEBUG: TestWorkerProcess {self.worker_name} run() called")
            time.sleep(0.1)
            print(f"iOS_DEBUG: TestWorkerProcess {self.worker_name} run() finished")

    try:
        wp = TestWorkerProcess("worker2")
        ui_updater.add_text_to_output(f"WorkerProcess created: {wp}\n")
        wp.start()
        ui_updater.add_text_to_output("WorkerProcess started\n")
        wp.join(timeout=2)
        ui_updater.add_text_to_output(
            f"WorkerProcess finished, exitcode: {wp.exitcode}\n"
        )
    except Exception as e:
        ui_updater.add_text_to_output(f"ERROR: {e}\n")
        import traceback

        ui_updater.add_text_to_output(f"Traceback: {traceback.format_exc()}\n")

    ui_updater.add_text_to_output("\nMultiprocessing tests completed\n")
