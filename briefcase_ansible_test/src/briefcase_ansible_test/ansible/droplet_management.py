"""
Digital Ocean droplet management functionality
"""

import os
import traceback
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible import context
from ansible.module_utils.common.collections import ImmutableDict

from .callbacks import SimpleCallback
from .play_executor import execute_play_with_timeout


def run_droplet_playbook(app_paths, ui_updater):
    """Run the rtorrent droplet creation playbook locally"""
    ui_updater.add_text_to_output("Starting rtorrent droplet creation...\n")
    
    # Load the API key
    api_key_file = os.path.join(
        app_paths.app, "resources", "api_keys", "do.api_key"
    )
    if not os.path.exists(api_key_file):
        ui_updater.add_text_to_output(f"❌ API key file not found: {api_key_file}\n")
        return False
        
    with open(api_key_file, 'r') as f:
        api_key = f.read().strip()
    ui_updater.add_text_to_output("✅ Digital Ocean API key loaded\n")
    
    # Path to inventory and playbook
    inventory_file = os.path.join(
        app_paths.app, "resources", "inventory", "sample_inventory.ini"
    )
    playbook_file = os.path.join(
        app_paths.app, "resources", "playbooks", "start_rtorrent_droplet.yml"
    )
    
    if not os.path.exists(playbook_file):
        ui_updater.add_text_to_output(f"❌ Playbook not found: {playbook_file}\n")
        return False
    
    ui_updater.add_text_to_output("✅ Playbook found\n")
    
    try:
        # Create data loader and load playbook
        loader = DataLoader()
        playbook_data = loader.load_from_file(playbook_file)
        
        # Set up inventory and variable manager
        inventory = InventoryManager(loader=loader, sources=[inventory_file])
        variable_manager = VariableManager(loader=loader, inventory=inventory)
        
        # Set extra variables including the API key
        variable_manager.extra_vars = {
            'digitalocean_token': api_key,
            'ssh_key': 'briefcase_ansible'
        }
        
        ui_updater.add_text_to_output("✅ Ansible components initialized\n")
        ui_updater.add_text_to_output("Extra vars: digitalocean_token=***masked***, ssh_key=briefcase_ansible\n")
        
        # Set up context for LOCAL execution (not paramiko)
        context.CLIARGS = ImmutableDict(
            connection="local",  # LOCAL connection, not paramiko
            module_path=[],
            forks=1,
            become=None,
            become_method=None,
            become_user=None,
            check=False,
            diff=False,
            verbosity=0,
            host_key_checking=False,
        )
        
        # Create Play from playbook data (use first play)
        if isinstance(playbook_data, list) and playbook_data:
            play_data = playbook_data[0]
        else:
            play_data = playbook_data
            
        play = Play().load(
            play_data, variable_manager=variable_manager, loader=loader
        )
        
        ui_updater.add_text_to_output(f"✅ Play loaded: {play.get_name()}\n")
        ui_updater.add_text_to_output(f"Play hosts: {play.hosts}\n")
        
        # Create callback plugin for output
        callback = SimpleCallback(ui_updater)
        
        # Execute the play locally
        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=inventory,
                variable_manager=variable_manager,
                loader=loader,
                passwords={},
                stdout_callback=callback,
            )
            
            ui_updater.add_text_to_output("Executing Digital Ocean droplet playbook locally...\n")
            
            # Execute with timeout
            result = execute_play_with_timeout(
                tqm, 
                play, 
                ui_updater.add_text_to_output,
                timeout=300  # 5 minute timeout for droplet creation
            )
            
            if result == 0:
                ui_updater.add_text_to_output("✅ Droplet creation completed successfully!\n")
                return True
            else:
                ui_updater.add_text_to_output(f"❌ Droplet creation failed with return code: {result}\n")
                return False
                
        finally:
            if tqm is not None:
                tqm.cleanup()
                
    except Exception as e:
        ui_updater.add_text_to_output(f"❌ Droplet creation failed: {e}\n")
        ui_updater.add_text_to_output(f"Traceback:\n{traceback.format_exc()}\n")
        return False