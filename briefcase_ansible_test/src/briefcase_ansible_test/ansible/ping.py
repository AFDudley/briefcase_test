"""
Ansible ping test functions for briefcase_ansible_test

This module contains functions for testing connectivity to Ansible hosts.
"""

import os
import sys
import threading
import traceback

# Import Ansible modules
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader


def ansible_ping_test(app, widget):
    """
    Run an Ansible ping module against the target host using the test SSH key.

    Args:
        app: The application instance
        widget: The widget that triggered this function
    """

    # Run in a background thread to keep UI responsive
    def run_in_background():
        try:
            # Target host configuration - use the group name to match inventory
            target_host = (
                "localhost"  # This matches the [localhost] group containing 127.0.0.1
            )
            # Get path to the SSH key
            key_path = os.path.join(
                app.paths.app, "resources", "keys", "briefcase_test_key"
            )

            # Import Ansible modules
            from ansible.module_utils.common.collections import ImmutableDict
            from ansible.inventory.manager import InventoryManager
            from ansible.vars.manager import VariableManager
            from ansible.playbook.play import Play
            from ansible.executor.task_queue_manager import TaskQueueManager
            from ansible.plugins.callback import CallbackBase
            from ansible import context
            from ansible.plugins.loader import init_plugin_loader

            # Simple callback for output
            class SimpleCallback(CallbackBase):
                def __init__(self, output_callback):
                    super().__init__()
                    self.output_callback = output_callback
                    self.host_ok = {}
                    self.host_failed = {}
                    self.host_unreachable = {}
                    # Thread debugging
                    import threading

                    self.main_thread_id = threading.get_ident()
                    self.output_callback(
                        f"🧵 Callback created on thread: {self.main_thread_id}\n"
                    )

                def v2_playbook_on_start(self, playbook):
                    self.output_callback("📖 Playbook started\n")

                def v2_playbook_on_play_start(self, play):
                    self.output_callback(f"🎭 Play started: {play.get_name()}\n")

                def v2_playbook_on_task_start(self, task, is_conditional):
                    self.output_callback(f"🔧 Task started: {task.get_name()}\n")

                def v2_runner_on_start(self, host, task):
                    self.output_callback(
                        f"🚀 Starting task on {host}: {task.get_name()}\n"
                    )

                def v2_runner_on_ok(self, result):
                    host = result._host.get_name()
                    self.host_ok[host] = result
                    self.output_callback(f"✅ {host} | PING => SUCCESS\n")

                def v2_runner_on_failed(self, result, ignore_errors=False):
                    host = result._host.get_name()
                    self.host_failed[host] = result
                    msg = result._result.get("msg", "unknown error")
                    self.output_callback(f"❌ {host} | PING => FAILED: {msg}\n")

                def v2_runner_on_unreachable(self, result):
                    host = result._host.get_name()
                    self.host_unreachable[host] = result
                    msg = result._result.get("msg", "unreachable")
                    self.output_callback(f"🔌 {host} | PING => UNREACHABLE: {msg}\n")

                def v2_runner_on_skipped(self, result):
                    host = result._host.get_name()
                    self.output_callback(f"⏭️  {host} | PING => SKIPPED\n")

                def v2_playbook_on_stats(self, stats):
                    self.output_callback("📊 Final stats:\n")
                    hosts = sorted(stats.processed.keys())
                    for host in hosts:
                        s = stats.summarize(host)
                        self.output_callback(
                            f"  {host}: ok={s['ok']}, changed={s['changed']}, unreachable={s['unreachable']}, failed={s['failures']}\n"
                        )

            # Path to the inventory file
            inventory_file = os.path.join(
                app.paths.app, "resources", "inventory", "sample_inventory.ini"
            )
            app.ui_updater.add_text_to_output(f"Using inventory: {inventory_file}\n")
            app.ui_updater.add_text_to_output(f"Using SSH key: {key_path}\n")
            app.ui_updater.add_text_to_output(f"Target: {target_host}\n\n")

            # Setup Ansible objects
            loader = DataLoader()
            inventory = InventoryManager(loader=loader, sources=[inventory_file])
            variable_manager = VariableManager(loader=loader, inventory=inventory)

            # Debug inventory contents
            all_hosts = inventory.get_hosts()
            app.ui_updater.add_text_to_output(
                f"Found {len(all_hosts)} total hosts in inventory\n"
            )
            for host in all_hosts:
                app.ui_updater.add_text_to_output(f"  Host: {host.name}\n")

            # Check if target host pattern matches any hosts
            target_hosts = inventory.get_hosts(pattern=target_host)
            app.ui_updater.add_text_to_output(
                f"Hosts matching '{target_host}': {len(target_hosts)}\n"
            )
            for host in target_hosts:
                app.ui_updater.add_text_to_output(f"  Matched host: {host.name}\n")

            # Create and configure options with SSH key
            context.CLIARGS = ImmutableDict(
                connection="local",  # Use local connection like in working test
                module_path=[],
                forks=1,  # Use forks=1 like in working test
                become=None,
                become_method=None,
                become_user=None,
                check=False,
                diff=False,
                verbosity=0,
                private_key_file=key_path,
                host_key_checking=False,
            )

            # Check multiprocessing availability
            app.ui_updater.add_text_to_output(
                "Checking multiprocessing availability...\n"
            )
            multiprocessing_modules = [
                "multiprocessing",
                "multiprocessing.synchronize",
                "_multiprocessing",
            ]

            for module_name in multiprocessing_modules:
                if module_name in sys.modules:
                    app.ui_updater.add_text_to_output(f"Found {module_name}\n")

            # Initialize plugin loader like the CLI does
            app.ui_updater.add_text_to_output("Initializing plugin loader...\n")
            try:
                init_plugin_loader()
                app.ui_updater.add_text_to_output("✅ Plugin loader initialized\n")
            except Exception as e:
                app.ui_updater.add_text_to_output(f"❌ Plugin loader failed: {e}\n")
                return

            # Patch WorkerProcess for debugging
            app.ui_updater.add_text_to_output(
                "Patching WorkerProcess for debugging...\n"
            )
            try:
                from briefcase_ansible_test.ansible_worker_debug import (
                    patch_worker_process_for_debugging,
                )

                if patch_worker_process_for_debugging():
                    app.ui_updater.add_text_to_output("✅ WorkerProcess patched\n")
                else:
                    app.ui_updater.add_text_to_output("⚠️ WorkerProcess patch failed\n")
            except Exception as e:
                app.ui_updater.add_text_to_output(
                    f"❌ WorkerProcess patch error: {e}\n"
                )

            # Patch connection plugins for debugging
            app.ui_updater.add_text_to_output("Patching connection plugins...\n")
            try:
                from briefcase_ansible_test.ansible_connection_debug import (
                    patch_connection_plugins,
                )

                if patch_connection_plugins():
                    app.ui_updater.add_text_to_output("✅ Connection plugins patched\n")
                else:
                    app.ui_updater.add_text_to_output(
                        "⚠️ Connection plugin patch failed\n"
                    )
            except Exception as e:
                app.ui_updater.add_text_to_output(
                    f"❌ Connection plugin patch error: {e}\n"
                )

            # Verify ping module is available
            try:
                from ansible.modules.ping import main as ping_main

                app.ui_updater.add_text_to_output("✅ Ping module available\n")
            except ImportError as e:
                app.ui_updater.add_text_to_output(
                    f"❌ Ping module not available: {e}\n"
                )
                return

            # Check what directories we have write access to
            import tempfile

            app.ui_updater.add_text_to_output("Checking directory access...\n")
            home_dir = os.path.expanduser("~")
            app.ui_updater.add_text_to_output(f"Home directory: {home_dir}\n")

            # Test write access to different directories
            test_dirs = [
                home_dir,
                os.path.join(home_dir, ".ansible"),
                tempfile.gettempdir(),
                (
                    app.paths.cache
                    if hasattr(app, "paths") and hasattr(app.paths, "cache")
                    else None
                ),
                (
                    app.paths.data
                    if hasattr(app, "paths") and hasattr(app.paths, "data")
                    else None
                ),
            ]

            writable_dir = None
            for test_dir in test_dirs:
                if test_dir is None:
                    continue
                try:
                    os.makedirs(test_dir, exist_ok=True)
                    # Test write access
                    test_file = os.path.join(test_dir, "test_write_access")
                    with open(test_file, "w") as f:
                        f.write("test")
                    os.remove(test_file)
                    app.ui_updater.add_text_to_output(
                        f"✅ Write access to: {test_dir}\n"
                    )
                    if writable_dir is None:
                        writable_dir = test_dir
                except Exception as e:
                    app.ui_updater.add_text_to_output(
                        f"❌ No write access to {test_dir}: {e}\n"
                    )

            # Set up Ansible temp directory in a writable location
            if writable_dir:
                ansible_tmp_dir = os.path.join(writable_dir, ".ansible", "tmp")
                app.ui_updater.add_text_to_output(
                    f"Using Ansible temp directory: {ansible_tmp_dir}\n"
                )
                try:
                    os.makedirs(ansible_tmp_dir, exist_ok=True)

                    # Configure Ansible to use our writable directory
                    from ansible import constants as C

                    # Set the temporary directory paths
                    C.DEFAULT_LOCAL_TMP = ansible_tmp_dir
                    C.DEFAULT_REMOTE_TMP = ansible_tmp_dir

                    # Also set environment variables as fallback
                    os.environ["ANSIBLE_LOCAL_TEMP"] = ansible_tmp_dir
                    os.environ["ANSIBLE_REMOTE_TEMP"] = ansible_tmp_dir
                    os.environ["TMPDIR"] = writable_dir  # Set system temp dir

                    app.ui_updater.add_text_to_output(
                        "✅ Ansible temp directory configured\n"
                    )
                except Exception as e:
                    app.ui_updater.add_text_to_output(
                        f"❌ Failed to create temp directory: {e}\n"
                    )
            else:
                app.ui_updater.add_text_to_output("❌ No writable directory found!\n")

            # Create play with ping task
            play_source = {
                "name": "Ansible Ping Test",
                "hosts": target_host,
                "gather_facts": False,
                "tasks": [{"name": "ping test", "ping": {}}],
            }

            # Create the Play
            app.ui_updater.add_text_to_output("Loading play definition...\n")
            try:
                play = Play().load(
                    play_source, variable_manager=variable_manager, loader=loader
                )
                app.ui_updater.add_text_to_output("✅ Play loaded successfully\n")

                # Debug play details
                app.ui_updater.add_text_to_output(f"Play hosts: {play.hosts}\n")
                app.ui_updater.add_text_to_output(f"Play tasks: {len(play.tasks)}\n")
                for i, task_block in enumerate(play.tasks):
                    app.ui_updater.add_text_to_output(f"  Block {i}: {task_block}\n")
                    if hasattr(task_block, "block"):
                        for j, task in enumerate(task_block.block):
                            app.ui_updater.add_text_to_output(
                                f"    Task {j}: {task.name} - {task.action}\n"
                            )

            except Exception as e:
                app.ui_updater.add_text_to_output(f"❌ Play load failed: {e}\n")
                app.ui_updater.add_text_to_output(
                    f"Traceback: {traceback.format_exc()}\n"
                )
                return

            # Create callback for output
            results_callback = SimpleCallback(app.ui_updater.add_text_to_output)

            # Run it with debugging - keeping mocks in place
            tqm = None
            try:
                app.ui_updater.add_text_to_output("Creating TaskQueueManager...\n")
                tqm = TaskQueueManager(
                    inventory=inventory,
                    variable_manager=variable_manager,
                    loader=loader,
                    passwords=dict(),
                    stdout_callback=results_callback,
                    forks=1,
                )

                app.ui_updater.add_text_to_output("Running playbook...\n")

                # Check multiprocessing.Process before running
                import multiprocessing

                print(
                    f"iOS_DEBUG: multiprocessing.Process is: {multiprocessing.Process}"
                )
                print(f"iOS_DEBUG: multiprocessing module: {multiprocessing}")

                try:
                    # Add timeout mechanism to prevent hanging
                    import threading

                    # Log to system for xcrun debugging
                    print(f"iOS_DEBUG: About to call tqm.run(), PID: {os.getpid()}")
                    print(
                        f"iOS_DEBUG: Current thread count: {threading.active_count()}"
                    )
                    print(f"iOS_DEBUG: Threading module: {threading}")

                    result = None
                    exception = None

                    def run_with_timeout():
                        nonlocal result, exception
                        try:
                            print(
                                "iOS_DEBUG: Inside timeout thread, about to call tqm.run()"
                            )

                            # Check if the strategy can see the hosts
                            print(
                                f"iOS_DEBUG: TQM inventory hosts: {[h.name for h in tqm._inventory.get_hosts()]}"
                            )
                            print(
                                f"iOS_DEBUG: TQM workers before run: {getattr(tqm, '_workers', 'not initialized')}"
                            )

                            # Check Queue types
                            import multiprocessing

                            print(
                                f"iOS_DEBUG: multiprocessing.Queue: {multiprocessing.Queue}"
                            )
                            test_q = multiprocessing.Queue()
                            print(
                                f"iOS_DEBUG: Test queue created: {test_q}, type: {type(test_q)}"
                            )

                            # Check if TQM has _final_q
                            if hasattr(tqm, "_final_q"):
                                print(
                                    f"iOS_DEBUG: TQM._final_q type: {type(tqm._final_q)}"
                                )

                            result = tqm.run(play)
                            print(
                                f"iOS_DEBUG: tqm.run() completed with result: {result}"
                            )
                        except Exception as e:
                            print(f"iOS_DEBUG: tqm.run() exception: {e}")
                            exception = e

                    timeout_thread = threading.Thread(target=run_with_timeout)
                    timeout_thread.start()
                    timeout_thread.join(timeout=10)  # 10 second timeout

                    if timeout_thread.is_alive():
                        app.ui_updater.add_text_to_output(
                            "⚠️ TQM.run() timed out after 10 seconds\n"
                        )
                        result = 1
                    elif exception:
                        raise exception
                    else:
                        app.ui_updater.add_text_to_output(
                            f"Playbook completed with result: {result}\n"
                        )
                except Exception as e:
                    app.ui_updater.add_text_to_output(f"❌ TQM.run() failed: {e}\n")
                    app.ui_updater.add_text_to_output(f"Exception type: {type(e)}\n")
                    app.ui_updater.add_text_to_output(
                        f"Traceback: {traceback.format_exc()}\n"
                    )
                    result = 1

                # Check if any hosts were processed
                if hasattr(results_callback, "host_ok"):
                    app.ui_updater.add_text_to_output(
                        f"Successful hosts: {len(getattr(results_callback, 'host_ok', {}))}\n"
                    )
                if hasattr(results_callback, "host_failed"):
                    app.ui_updater.add_text_to_output(
                        f"Failed hosts: {len(getattr(results_callback, 'host_failed', {}))}\n"
                    )
                if hasattr(results_callback, "host_unreachable"):
                    app.ui_updater.add_text_to_output(
                        f"Unreachable hosts: {len(getattr(results_callback, 'host_unreachable', {}))}\n"
                    )

                if result == 0:
                    app.ui_updater.update_status("Success")
                else:
                    app.ui_updater.update_status("Failed")

            finally:
                if tqm is not None:
                    app.ui_updater.add_text_to_output(
                        "Cleaning up TaskQueueManager...\n"
                    )
                    tqm.cleanup()

        except Exception as error:
            app.ui_updater.add_text_to_output(f"Error: {str(error)}\n")
            app.ui_updater.add_text_to_output(f"Traceback: {traceback.format_exc()}\n")
            app.ui_updater.update_status("Error")

    # Run the task in a background thread
    app.background_task_runner.run_task(
        run_in_background, "Running Ansible ping test..."
    )
