"""
Debug helper to patch WorkerProcess for better error visibility
"""


def patch_worker_process_for_debugging():
    """Patch WorkerProcess to add debugging before it exits"""
    try:
        from ansible.executor.process.worker import WorkerProcess

        # Store original methods
        original_init = WorkerProcess.__init__
        original_run = WorkerProcess._run

        def debug_init(self, *args, **kwargs):
            print(
                "iOS_DEBUG: WorkerProcess.__init__ called with "
                + str(len(args))
                + " args"
            )
            try:
                # Call original init
                original_init(self, *args, **kwargs)
                print("iOS_DEBUG: WorkerProcess.__init__ completed successfully")

                # Log what we received
                print(
                    "iOS_DEBUG: Worker ID: "
                    + str(getattr(self, "_worker_id", "NOT SET"))
                )
                print("iOS_DEBUG: Host: " + str(getattr(self, "_host", "NOT SET")))
                print("iOS_DEBUG: Task: " + str(getattr(self, "_task", "NOT SET")))
                print(
                    "iOS_DEBUG: Final queue type: "
                    + str(type(getattr(self, "_final_q", None)))
                )

            except Exception as e:
                print("iOS_DEBUG: WorkerProcess.__init__ failed: " + str(e))
                import traceback

                print("iOS_DEBUG: Init traceback:\n" + traceback.format_exc())
                raise

        def debug_run(self):
            print("iOS_DEBUG: WorkerProcess._run() called")
            print("iOS_DEBUG: Worker attributes check:")
            print("  - _host: " + str(hasattr(self, "_host")))
            print("  - _task: " + str(hasattr(self, "_task")))
            print("  - _loader: " + str(hasattr(self, "_loader")))
            print("  - _final_q: " + str(hasattr(self, "_final_q")))
            print("  - _variable_manager: " + str(hasattr(self, "_variable_manager")))

            try:
                # Check display import
                print("iOS_DEBUG: Importing display...")
                from ansible.utils.display import Display

                display = Display()
                print("iOS_DEBUG: Display imported successfully")

                # Check queue setting
                if hasattr(self, "_final_q"):
                    print(
                        "iOS_DEBUG: Setting display queue to "
                        + str(type(self._final_q))
                    )
                    display.set_queue(self._final_q)
                    print("iOS_DEBUG: Display queue set successfully")
                else:
                    print("iOS_DEBUG: ERROR: No _final_q attribute!")

                # Call original run
                print("iOS_DEBUG: Calling original _run()")
                result = original_run(self)
                print("iOS_DEBUG: WorkerProcess._run() completed successfully")
                return result

            except Exception as e:
                print("iOS_DEBUG: WorkerProcess._run() exception: " + str(e))
                print("iOS_DEBUG: Exception type: " + str(type(e)))
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
