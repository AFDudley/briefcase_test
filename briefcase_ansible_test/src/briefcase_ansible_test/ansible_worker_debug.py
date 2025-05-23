"""
Debug helper to patch WorkerProcess for better error visibility
"""

import sys


def patch_worker_process_for_debugging():
    """Patch WorkerProcess to add debugging before it exits"""
    try:
        from ansible.executor.process.worker import WorkerProcess

        # Store original methods
        original_init = WorkerProcess.__init__
        original_run = WorkerProcess._run

        def debug_init(self, *args, **kwargs):
            print(f"iOS_DEBUG: WorkerProcess.__init__ called with {len(args)} args")
            try:
                # Call original init
                original_init(self, *args, **kwargs)
                print(f"iOS_DEBUG: WorkerProcess.__init__ completed successfully")

                # Log what we received
                print(f"iOS_DEBUG: Worker ID: {getattr(self, '_worker_id', 'NOT SET')}")
                print(f"iOS_DEBUG: Host: {getattr(self, '_host', 'NOT SET')}")
                print(f"iOS_DEBUG: Task: {getattr(self, '_task', 'NOT SET')}")
                print(
                    f"iOS_DEBUG: Final queue type: {type(getattr(self, '_final_q', None))}"
                )

            except Exception as e:
                print(f"iOS_DEBUG: WorkerProcess.__init__ failed: {e}")
                import traceback

                print(f"iOS_DEBUG: Init traceback:\n{traceback.format_exc()}")
                raise

        def debug_run(self):
            print(f"iOS_DEBUG: WorkerProcess._run() called")
            print(f"iOS_DEBUG: Worker attributes check:")
            print(f"  - _host: {hasattr(self, '_host')}")
            print(f"  - _task: {hasattr(self, '_task')}")
            print(f"  - _loader: {hasattr(self, '_loader')}")
            print(f"  - _final_q: {hasattr(self, '_final_q')}")
            print(f"  - _variable_manager: {hasattr(self, '_variable_manager')}")

            try:
                # Check display import
                print(f"iOS_DEBUG: Importing display...")
                from ansible.utils.display import Display

                display = Display()
                print(f"iOS_DEBUG: Display imported successfully")

                # Check queue setting
                if hasattr(self, "_final_q"):
                    print(f"iOS_DEBUG: Setting display queue to {type(self._final_q)}")
                    display.set_queue(self._final_q)
                    print(f"iOS_DEBUG: Display queue set successfully")
                else:
                    print(f"iOS_DEBUG: ERROR: No _final_q attribute!")

                # Call original run
                print(f"iOS_DEBUG: Calling original _run()")
                result = original_run(self)
                print(f"iOS_DEBUG: WorkerProcess._run() completed successfully")
                return result

            except Exception as e:
                print(f"iOS_DEBUG: WorkerProcess._run() exception: {e}")
                print(f"iOS_DEBUG: Exception type: {type(e)}")
                import traceback

                print(f"iOS_DEBUG: Run traceback:\n{traceback.format_exc()}")
                raise

        # Apply patches
        WorkerProcess.__init__ = debug_init
        WorkerProcess._run = debug_run

        print("iOS_DEBUG: WorkerProcess patched for debugging")
        return True

    except Exception as e:
        print(f"iOS_DEBUG: Failed to patch WorkerProcess: {e}")
        return False
