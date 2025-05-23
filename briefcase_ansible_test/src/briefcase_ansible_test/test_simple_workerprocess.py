"""
Simple test to verify WorkerProcess can be instantiated and run on iOS.

This bypasses all the Ansible collection/plugin loading complexity
and just tests the core WorkerProcess functionality.
"""


def test_simple_workerprocess(ui_updater):
    """Test WorkerProcess with minimal dependencies"""
    ui_updater.add_text_to_output("Testing Simple WorkerProcess...\n")
    
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
    
    try:
        # Import WorkerProcess
        ui_updater.add_text_to_output("\nImporting WorkerProcess...\n")
        from ansible.executor.process.worker import WorkerProcess
        ui_updater.add_text_to_output("✅ WorkerProcess imported successfully\n")
        
        # Import our queue
        from briefcase_ansible_test.utils.multiprocessing.queues import ProcessQueue
        
        # Create a minimal task-like object
        class FakeTask:
            def __init__(self):
                self.action = 'debug'
                self.args = {'msg': 'Hello from iOS!'}
                self._uuid = 'test-task-123'
                self.name = 'Test Task'
                
            def get_name(self):
                return self.name
                
            def get_vars(self):
                return {}
        
        # Create a minimal host-like object
        class FakeHost:
            def __init__(self):
                self.name = 'localhost'
                self.vars = {}
                
            def get_name(self):
                return self.name
                
            def get_vars(self):
                return self.vars
        
        # Create a minimal loader-like object
        class FakeLoader:
            def __init__(self):
                self._tempfiles = set()
        
        # Create minimal required objects
        task = FakeTask()
        host = FakeHost()
        loader = FakeLoader()
        final_q = ProcessQueue()
        
        ui_updater.add_text_to_output("\nCreating WorkerProcess with minimal args...\n")
        ui_updater.add_text_to_output(f"Loader: {loader}\n")
        ui_updater.add_text_to_output(f"Loader type: {type(loader)}\n")
        ui_updater.add_text_to_output(f"Loader has _tempfiles: {hasattr(loader, '_tempfiles')}\n")
        
        # WorkerProcess args: final_q, task, host, task_vars, play_context, loader, variable_manager, shared_loader_obj, worker_id
        # We'll pass None for most complex objects
        worker = WorkerProcess(
            final_q=final_q,
            task=task,
            host=host,
            task_vars={},
            play_context=None,  # Will likely cause issues but let's see
            loader=loader,  # Use our fake loader
            variable_manager=None,
            shared_loader_obj={},
            worker_id=1,  # Add the missing worker_id
        )
        
        ui_updater.add_text_to_output(f"✅ WorkerProcess created: {worker}\n")
        ui_updater.add_text_to_output(f"  Type: {type(worker)}\n")
        ui_updater.add_text_to_output(f"  Name: {worker.name if hasattr(worker, 'name') else 'N/A'}\n")
        
        # Try to start it (this will likely fail but let's see how)
        ui_updater.add_text_to_output("\nAttempting to start WorkerProcess...\n")
        worker.start()
        ui_updater.add_text_to_output("✅ WorkerProcess.start() called\n")
        
        # Wait briefly
        worker.join(timeout=1)
        
        if worker.is_alive():
            ui_updater.add_text_to_output("⚠️ WorkerProcess still running\n")
        else:
            ui_updater.add_text_to_output(f"WorkerProcess finished with exitcode: {worker.exitcode}\n")
        
        # Check queue for any output
        ui_updater.add_text_to_output("\nChecking queue for results...\n")
        try:
            result = final_q.get(timeout=0.5)
            ui_updater.add_text_to_output(f"Got result from queue: {result}\n")
        except:
            ui_updater.add_text_to_output("No result in queue\n")
            
    except Exception as e:
        ui_updater.add_text_to_output(f"\n❌ Error: {e}\n")
        ui_updater.add_text_to_output(f"Type: {type(e)}\n")
        import traceback
        ui_updater.add_text_to_output(f"Traceback:\n{traceback.format_exc()}\n")
    
    ui_updater.add_text_to_output("\nTest complete.\n")