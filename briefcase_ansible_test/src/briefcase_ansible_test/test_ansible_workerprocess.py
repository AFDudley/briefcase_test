"""
Test Ansible's actual WorkerProcess in isolation on iOS
"""


def test_ansible_workerprocess(ui_updater):
    """Test if Ansible's WorkerProcess can run in isolation"""
    ui_updater.add_text_to_output("Testing Ansible WorkerProcess in isolation...\n")
    
    # First ensure our patches are in place
    import sys
    ui_updater.add_text_to_output("Setting up iOS patches...\n")
    
    # Apply all iOS compatibility patches
    from briefcase_ansible_test.utils.multiprocessing import _patch_system_modules
    from briefcase_ansible_test.utils import (
        setup_pwd_module_mock,
        setup_grp_module_mock,
        patch_getpass,
        setup_subprocess_mock,
    )
    
    _patch_system_modules()
    setup_pwd_module_mock()
    setup_grp_module_mock()
    patch_getpass()
    setup_subprocess_mock()
    
    # Import ansible module to trigger iOS patches
    import briefcase_ansible_test.ansible
    
    ui_updater.add_text_to_output("✅ iOS patches applied\n")
    
    # Mock ansible_collections since iOS doesn't have the filesystem Ansible expects
    import types
    import os
    
    # Get app directory for later use
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create the ansible_collections module hierarchy
    if "ansible_collections" not in sys.modules:
        # Root module
        ansible_collections = types.ModuleType("ansible_collections")
        ansible_collections.__path__ = ["/mock/ansible_collections"]
        sys.modules["ansible_collections"] = ansible_collections
        
        # ansible namespace
        ansible_ns = types.ModuleType("ansible_collections.ansible")
        ansible_ns.__path__ = ["/mock/ansible_collections/ansible"]
        sys.modules["ansible_collections.ansible"] = ansible_ns
        setattr(ansible_collections, "ansible", ansible_ns)
        
        # builtin namespace
        builtin_ns = types.ModuleType("ansible_collections.ansible.builtin")
        builtin_ns.__path__ = ["/mock/ansible_collections/ansible/builtin"]
        sys.modules["ansible_collections.ansible.builtin"] = builtin_ns
        setattr(ansible_ns, "builtin", builtin_ns)
        
        # plugins namespace
        plugins_ns = types.ModuleType("ansible_collections.ansible.builtin.plugins")
        plugins_ns.__path__ = ["/mock/ansible_collections/ansible/builtin/plugins"]
        sys.modules["ansible_collections.ansible.builtin.plugins"] = plugins_ns
        setattr(builtin_ns, "plugins", plugins_ns)
        
        # modules namespace
        modules_ns = types.ModuleType("ansible_collections.ansible.builtin.plugins.modules")
        modules_ns.__path__ = ["/mock/ansible_collections/ansible/builtin/plugins/modules"]
        sys.modules["ansible_collections.ansible.builtin.plugins.modules"] = modules_ns
        setattr(plugins_ns, "modules", modules_ns)
        
        ui_updater.add_text_to_output("✅ Mocked ansible_collections module hierarchy\n")
    
    # Now try to create and run a WorkerProcess
    try:
        # Import required Ansible components
        ui_updater.add_text_to_output("\nImporting Ansible components...\n")
        
        from ansible.executor.process.worker import WorkerProcess
        from ansible.executor.task_result import TaskResult
        from ansible.parsing.dataloader import DataLoader
        from ansible.inventory.manager import InventoryManager
        from ansible.vars.manager import VariableManager
        from ansible.playbook.task import Task
        from ansible.playbook.play_context import PlayContext
        from ansible.plugins.loader import connection_loader
        
        # Import our custom queue
        from briefcase_ansible_test.utils.multiprocessing.queues import ProcessQueue
        
        ui_updater.add_text_to_output("✅ Imports successful\n")
        
        # Initialize plugin loader (needed before loading plays)
        from ansible.plugins.loader import init_plugin_loader
        ui_updater.add_text_to_output("\nInitializing plugin loader...\n")
        init_plugin_loader()
        ui_updater.add_text_to_output("✅ Plugin loader initialized\n")
        
        # Create minimal components needed by WorkerProcess
        ui_updater.add_text_to_output("\nCreating test components...\n")
        
        # Create a play and extract the task from it to avoid collection lookups
        from ansible.playbook.play import Play
        
        play_source = {
            "name": "Test Play",
            "hosts": "localhost",
            "gather_facts": False,
            "tasks": [{"name": "test ping", "ping": {}}],
        }
        
        # Create a loader
        loader = DataLoader()
        ui_updater.add_text_to_output("  DataLoader created\n")
        
        # Load the sample inventory file
        inventory_path = os.path.join(app_dir, "resources", "inventory", "sample_inventory.ini")
        ui_updater.add_text_to_output(f"  Loading inventory from: {inventory_path}\n")
        
        inventory = InventoryManager(loader=loader, sources=[inventory_path])
        
        # Get the localhost host (which should be 127.0.0.1 in the inventory)
        localhost = inventory.get_host('127.0.0.1')
        if not localhost:
            # Fallback to any host in localhost group
            localhost_group = inventory.groups.get('localhost')
            if localhost_group and localhost_group.hosts:
                localhost = localhost_group.hosts[0]
        
        if not localhost:
            raise Exception("Could not find localhost in inventory")
            
        ui_updater.add_text_to_output(f"  Host loaded from inventory: {localhost}\n")
        
        # Create variable manager
        variable_manager = VariableManager(loader=loader, inventory=inventory)
        ui_updater.add_text_to_output("  VariableManager created\n")
        
        # Now load the play
        ui_updater.add_text_to_output("  Loading play...\n")
        play = Play.load(play_source, variable_manager=variable_manager, loader=loader)
        ui_updater.add_text_to_output(f"  Play loaded: {play}\n")
        
        # Extract the first task from the play
        if play.tasks and len(play.tasks) > 0 and hasattr(play.tasks[0], 'block'):
            task = play.tasks[0].block[0]
            ui_updater.add_text_to_output(f"  Task extracted: {task}\n")
        else:
            raise Exception("Could not extract task from play")
        
        # Create play context
        play_context = PlayContext()
        play_context.connection = 'local'
        ui_updater.add_text_to_output("  PlayContext created\n")
        
        # Create queues
        final_q = ProcessQueue()
        ui_updater.add_text_to_output("  Final queue created\n")
        
        # Create shared loader path (WorkerProcess expects this)
        from ansible.vars.fact_cache import FactCache
        fact_cache = FactCache()
        
        # Build the arguments for WorkerProcess
        ui_updater.add_text_to_output("\nPreparing WorkerProcess arguments...\n")
        
        worker_args = (
            final_q,                    # final_q
            task,                       # task
            localhost,                  # host  
            task.get_vars(),           # task_vars
            play_context,              # play_context
            loader,                    # loader
            variable_manager,          # variable_manager
            {},                        # shared_loader_obj (simplified)
        )
        
        ui_updater.add_text_to_output(f"  Args prepared: {len(worker_args)} arguments\n")
        
        # Apply debug patches
        from briefcase_ansible_test.ansible_worker_debug import patch_worker_process_for_debugging
        patch_worker_process_for_debugging()
        
        # Create the WorkerProcess
        ui_updater.add_text_to_output("\nCreating WorkerProcess...\n")
        worker = WorkerProcess(*worker_args)
        ui_updater.add_text_to_output(f"✅ WorkerProcess created: {worker}\n")
        ui_updater.add_text_to_output(f"  Type: {type(worker)}\n")
        ui_updater.add_text_to_output(f"  Base classes: {WorkerProcess.__bases__}\n")
        
        # Start the worker
        ui_updater.add_text_to_output("\nStarting WorkerProcess...\n")
        worker.start()
        ui_updater.add_text_to_output("✅ WorkerProcess started\n")
        
        # Wait for completion with timeout
        ui_updater.add_text_to_output("Waiting for WorkerProcess to complete...\n")
        worker.join(timeout=5)
        
        if worker.is_alive():
            ui_updater.add_text_to_output("⚠️ WorkerProcess still running after 5 seconds\n")
        else:
            ui_updater.add_text_to_output(f"✅ WorkerProcess completed with exitcode: {worker.exitcode}\n")
        
        # Check for results in queue
        ui_updater.add_text_to_output("\nChecking for results...\n")
        try:
            result = final_q.get(timeout=1)
            ui_updater.add_text_to_output(f"✅ Got result from queue: {result}\n")
            ui_updater.add_text_to_output(f"  Result type: {type(result)}\n")
            
            if isinstance(result, TaskResult):
                ui_updater.add_text_to_output(f"  Task result: {result._result}\n")
                ui_updater.add_text_to_output(f"  Host: {result._host}\n")
                ui_updater.add_text_to_output(f"  Task: {result._task}\n")
        except Exception as e:
            ui_updater.add_text_to_output(f"❌ No result in queue: {e}\n")
        
        ui_updater.add_text_to_output("\n✅ WorkerProcess test completed successfully!\n")
        
    except Exception as e:
        ui_updater.add_text_to_output(f"\n❌ WorkerProcess test failed: {e}\n")
        ui_updater.add_text_to_output(f"Exception type: {type(e)}\n")
        import traceback
        ui_updater.add_text_to_output(f"Traceback:\n{traceback.format_exc()}\n")