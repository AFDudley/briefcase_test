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
            target_host = "localhost"  # This matches the [localhost] group containing 127.0.0.1
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
                    self.output_callback(f"🧵 Callback created on thread: {self.main_thread_id}\n")

                def v2_playbook_on_start(self, playbook):
                    self.output_callback("📖 Playbook started\n")

                def v2_playbook_on_play_start(self, play):
                    self.output_callback(f"🎭 Play started: {play.get_name()}\n")

                def v2_playbook_on_task_start(self, task, is_conditional):
                    self.output_callback(f"🔧 Task started: {task.get_name()}\n")

                def v2_runner_on_start(self, host, task):
                    self.output_callback(f"🚀 Starting task on {host}: {task.get_name()}\n")

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
                        self.output_callback(f"  {host}: ok={s['ok']}, changed={s['changed']}, unreachable={s['unreachable']}, failed={s['failures']}\n")

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
            app.ui_updater.add_text_to_output(f"Found {len(all_hosts)} total hosts in inventory\n")
            for host in all_hosts:
                app.ui_updater.add_text_to_output(f"  Host: {host.name}\n")
                
            # Check if target host pattern matches any hosts
            target_hosts = inventory.get_hosts(pattern=target_host)
            app.ui_updater.add_text_to_output(f"Hosts matching '{target_host}': {len(target_hosts)}\n")
            for host in target_hosts:
                app.ui_updater.add_text_to_output(f"  Matched host: {host.name}\n")

            # Create and configure options with SSH key
            context.CLIARGS = ImmutableDict(
                connection="local",  # Use local connection for localhost
                module_path=[],
                forks=1,  # Set to 1 to force serial execution without multiprocessing
                become=None,
                become_method=None,
                become_user=None,
                check=False,
                diff=False,
                verbosity=0,
                private_key_file=key_path,
                host_key_checking=False,
            )
            
            # Temporarily disable multiprocessing mocks for Ansible execution
            app.ui_updater.add_text_to_output("Checking multiprocessing mocks...\n")
            original_modules = {}
            multiprocessing_modules = ['multiprocessing', 'multiprocessing.synchronize', '_multiprocessing']
            
            for module_name in multiprocessing_modules:
                if module_name in sys.modules:
                    original_modules[module_name] = sys.modules[module_name]
                    app.ui_updater.add_text_to_output(f"Found mock for {module_name}\n")
            
            # Initialize plugin loader like the CLI does
            app.ui_updater.add_text_to_output("Initializing plugin loader...\n")
            try:
                init_plugin_loader()
                app.ui_updater.add_text_to_output("✅ Plugin loader initialized\n")
            except Exception as e:
                app.ui_updater.add_text_to_output(f"❌ Plugin loader failed: {e}\n")
                return

            # Verify ping module is available
            try:
                from ansible.modules.ping import main as ping_main
                app.ui_updater.add_text_to_output("✅ Ping module available\n")
            except ImportError as e:
                app.ui_updater.add_text_to_output(f"❌ Ping module not available: {e}\n")
                return

            # Create play with ping task - use exact same structure as ansible command
            play_source = {
                'name': "Ansible Ping Test",
                'hosts': target_host,
                'gather_facts': 'no',
                'tasks': [{'action': {'module': 'ping', 'args': {}}}]
            }

            # Create the Play
            app.ui_updater.add_text_to_output("Loading play definition...\n")
            try:
                play = Play().load(
                    play_source, variable_manager=variable_manager, loader=loader
                )
                app.ui_updater.add_text_to_output("✅ Play loaded successfully\n")
            except Exception as e:
                app.ui_updater.add_text_to_output(f"❌ Play load failed: {e}\n")
                app.ui_updater.add_text_to_output(f"Traceback: {traceback.format_exc()}\n")
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
                    forks=1,  # Force single process execution directly in TQM
                )
                
                app.ui_updater.add_text_to_output("Running playbook...\n")
                app.ui_updater.add_text_to_output(f"Debug: TQM forks setting: {getattr(tqm, '_forks', 'unknown')}\n")
                
                try:
                    result = tqm.run(play)
                    app.ui_updater.add_text_to_output(f"Playbook completed with result: {result}\n")
                except Exception as e:
                    app.ui_updater.add_text_to_output(f"❌ TQM.run() failed: {e}\n")
                    app.ui_updater.add_text_to_output(f"Exception type: {type(e)}\n")
                    app.ui_updater.add_text_to_output(f"Traceback: {traceback.format_exc()}\n")
                    result = 1
                
                # Check if any hosts were processed
                if hasattr(results_callback, 'host_ok'):
                    app.ui_updater.add_text_to_output(f"Successful hosts: {len(getattr(results_callback, 'host_ok', {}))}\n")
                if hasattr(results_callback, 'host_failed'): 
                    app.ui_updater.add_text_to_output(f"Failed hosts: {len(getattr(results_callback, 'host_failed', {}))}\n")
                if hasattr(results_callback, 'host_unreachable'):
                    app.ui_updater.add_text_to_output(f"Unreachable hosts: {len(getattr(results_callback, 'host_unreachable', {}))}\n")

                if result == 0:
                    app.ui_updater.update_status("Success")
                else:
                    app.ui_updater.update_status("Failed")

            finally:
                if tqm is not None:
                    app.ui_updater.add_text_to_output("Cleaning up TaskQueueManager...\n")
                    tqm.cleanup()

        except Exception as error:
            app.ui_updater.add_text_to_output(f"Error: {str(error)}\n")
            app.ui_updater.add_text_to_output(f"Traceback: {traceback.format_exc()}\n")
            app.ui_updater.update_status("Error")

    # Run the task in a background thread
    app.background_task_runner.run_task(
        run_in_background, "Running Ansible ping test..."
    )


