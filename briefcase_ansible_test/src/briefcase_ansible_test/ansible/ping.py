"""
Ansible ping test functions for briefcase_ansible_test

This module contains functions for testing connectivity to Ansible hosts.
"""

import os
import threading
import traceback

# Ensure system mocks are set up before importing Ansible
from briefcase_ansible_test.utils.system_utils import (
    patch_getpass,
    setup_pwd_module_mock,
    setup_grp_module_mock
)

# Apply patches that might be needed by Ansible imports
patch_getpass()
setup_pwd_module_mock()
setup_grp_module_mock()

def ansible_ping_test_with_key(self, widget):
    """
    Run an Ansible ping module against night2 using the ED25519 key.
    
    Args:
        self: The application instance
        widget: The widget that triggered this function
    """
    # Clear output and update status
    self.output_view.value = ""
    self.status_label.text = "Running Ansible ping test with ED25519 key..."

    # Run in a background thread to keep UI responsive
    def run_in_background():
        try:
            # Check if we have a key
            ssh_dir = os.path.join(self.paths.app, 'resources', 'ssh')
            private_key_path = os.path.join(ssh_dir, 'id_ed25519')

            if not os.path.exists(private_key_path):
                self.add_text_to_output("ED25519 private key not found.\n")
                self.add_text_to_output(f"Expected path: {private_key_path}\n")
                self.add_text_to_output("Please generate a key first.\n")
                self.update_status("Failed")
                return

            # Make sure the permissions are correct (iOS may have reset them)
            os.chmod(private_key_path, 0o600)
            self.add_text_to_output("Using private key: " + private_key_path + "\n")

            # Import Ansible modules
            from ansible.module_utils.common.collections import ImmutableDict
            from ansible.parsing.dataloader import DataLoader
            from ansible.inventory.manager import InventoryManager
            from ansible.vars.manager import VariableManager
            from ansible.playbook.play import Play
            from ansible.executor.task_queue_manager import TaskQueueManager
            from ansible.plugins.callback import CallbackBase
            from ansible import context

            # Define callback to capture output (same as before)
            class ResultCallback(CallbackBase):
                def __init__(self, output_callback):
                    super(ResultCallback, self).__init__()
                    self.output_callback = output_callback
                    self.host_ok = {}
                    self.host_failed = {}
                    self.host_unreachable = {}

                def v2_runner_on_ok(self, result):
                    host = result._host.get_name()
                    self.host_ok[host] = result
                    output = f"{host} | SUCCESS => {{\n"
                    output += f"    \"changed\": {str(result._result.get('changed', False)).lower()},\n"
                    if 'ansible_facts' in result._result:
                        output += "    \"ansible_facts\": {\n"
                        for k, v in result._result['ansible_facts'].items():
                            output += f"        \"{k}\": \"{v}\",\n"
                        output += "    },\n"
                    output += f"    \"ping\": \"{result._result.get('ping', '')}\"\n"
                    output += "}\n"
                    self.output_callback(output)

                def v2_runner_on_failed(self, result, ignore_errors=False):
                    host = result._host.get_name()
                    self.host_failed[host] = result
                    output = f"{host} | FAILED => {{\n"
                    output += f"    \"msg\": \"{result._result.get('msg', 'unknown error')}\"\n"
                    output += "}\n"
                    self.output_callback(output)

                def v2_runner_on_unreachable(self, result):
                    host = result._host.get_name()
                    self.host_unreachable[host] = result
                    output = f"{host} | UNREACHABLE => {{\n"
                    output += f"    \"msg\": \"{result._result.get('msg', 'unreachable')}\"\n"
                    output += "}\n"
                    self.output_callback(output)

            # Path to the inventory file
            inventory_file = os.path.join(self.paths.app, 'resources', 'inventory', 'sample_inventory.ini')
            self.add_text_to_output(f"Using inventory: {inventory_file}\n")
            self.add_text_to_output("Target: night2\n\n")

            # Setup Ansible objects
            loader = DataLoader()
            inventory = InventoryManager(loader=loader, sources=[inventory_file])
            variable_manager = VariableManager(loader=loader, inventory=inventory)

            # Create and configure options with SSH key
            context.CLIARGS = ImmutableDict(
                connection='ssh',
                module_path=[],
                forks=10,
                become=None,
                become_method=None,
                become_user=None,
                check=False,
                diff=False,
                verbosity=0,
                private_key_file=private_key_path
            )

            # private_key_file parameter in CLIARGS will be used by Ansible

            # Create play with ping task
            play_source = dict(
                name="Ansible Ping with ED25519 Key",
                hosts="night2",
                gather_facts=False,
                tasks=[dict(action=dict(module='ping'))]
            )

            # Create the Play
            play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

            # Create callback for output
            results_callback = ResultCallback(self.add_text_to_output)

            # Run it
            tqm = None
            try:
                tqm = TaskQueueManager(
                    inventory=inventory,
                    variable_manager=variable_manager,
                    loader=loader,
                    passwords=dict(),
                    stdout_callback=results_callback
                )

                result = tqm.run(play)

                if result == 0:
                    self.update_status("Success")
                else:
                    self.update_status("Failed")

            finally:
                if tqm is not None:
                    tqm.cleanup()

        except Exception as error:
            self.add_text_to_output(f"Error running Ansible ping: {str(error)}\n")
            self.add_text_to_output(f"Traceback: {traceback.format_exc()}\n")
            self.update_status("Error")

    # Start background thread
    thread = threading.Thread(target=run_in_background)
    thread.daemon = True
    thread.start()