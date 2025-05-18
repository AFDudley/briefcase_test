"""
A test to get ansible running in briefcase
"""

import os
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW


class briefcase_ansible_test(toga.App):
    def startup(self):
        """Construct and show the Toga application with Ansible functionality."""
        # Create main box with vertical layout
        main_box = toga.Box(style=Pack(direction=COLUMN, margin=10))
        
        # Create playbook section
        playbook_box = toga.Box(style=Pack(direction=ROW, margin=5))
        playbook_box.add(toga.Label('Playbook:', style=Pack(margin=(0, 5))))
        self.playbook_path = toga.TextInput(readonly=True, style=Pack(flex=1))
        playbook_box.add(self.playbook_path)
        playbook_button = toga.Button('Browse...', on_press=self.select_playbook)
        playbook_box.add(playbook_button)
        
        # Create inventory section
        inventory_box = toga.Box(style=Pack(direction=ROW, margin=5))
        inventory_box.add(toga.Label('Inventory:', style=Pack(margin=(0, 5))))
        self.inventory_path = toga.TextInput(readonly=True, style=Pack(flex=1))
        inventory_box.add(self.inventory_path)
        inventory_button = toga.Button('Browse...', on_press=self.select_inventory)
        inventory_box.add(inventory_button)
        
        # Create default playbooks directory
        self.playbooks_dir = os.path.join(self.paths.app, 'playbooks')
        self.inventory_dir = os.path.join(self.paths.app, 'inventory')
        
        # Create directories if they don't exist
        os.makedirs(self.playbooks_dir, exist_ok=True)
        os.makedirs(self.inventory_dir, exist_ok=True)
        
        # Create a sample playbook and inventory if they don't exist
        self.create_sample_files()
        
        # Run button
        run_button = toga.Button('Run Playbook', on_press=self.run_playbook, style=Pack(margin=5))
        
        # Status and output
        self.status_label = toga.Label('Ready', style=Pack(margin=5))
        self.output_view = toga.MultilineTextInput(readonly=True, style=Pack(flex=1, margin=5))
        
        # Add components to main box
        main_box.add(toga.Label('Ansible Runner', style=Pack(text_align='center', font_size=16, margin=10)))
        main_box.add(playbook_box)
        main_box.add(inventory_box)
        main_box.add(run_button)
        main_box.add(self.status_label)
        main_box.add(self.output_view)
        
        # Set up the main window
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()
    
    def create_sample_files(self):
        """Create sample playbook and inventory files"""
        # Sample playbook
        sample_playbook_path = os.path.join(self.playbooks_dir, 'sample_playbook.yml')
        if not os.path.exists(sample_playbook_path):
            with open(sample_playbook_path, 'w') as f:
                f.write("""---
- name: Sample Playbook
  hosts: all
  gather_facts: false
  tasks:
    - name: Hello World
      debug:
        msg: "Hello from Ansible in Briefcase!"
""")
        
        # Sample inventory
        sample_inventory_path = os.path.join(self.inventory_dir, 'sample_inventory.ini')
        if not os.path.exists(sample_inventory_path):
            with open(sample_inventory_path, 'w') as f:
                f.write("""[local]
localhost ansible_connection=local
""")
    
    def select_playbook(self, widget):
        """Open a file dialog to select a playbook file"""
        try:
            playbook_file = self.main_window.open_file_dialog(
                title="Select Playbook",
                initial_directory=self.playbooks_dir,
                file_types=[('YAML Files', '*.yml'), ('YAML Files', '*.yaml'), ('All Files', '*')]
            )
            if playbook_file:
                self.playbook_path.value = playbook_file
        except Exception as e:
            self.status_label.text = f"Error selecting playbook: {str(e)}"
    
    def select_inventory(self, widget):
        """Open a file dialog to select an inventory file"""
        try:
            inventory_file = self.main_window.open_file_dialog(
                title="Select Inventory",
                initial_directory=self.inventory_dir,
                file_types=[('Inventory Files', '*.ini'), ('All Files', '*')]
            )
            if inventory_file:
                self.inventory_path.value = inventory_file
        except Exception as e:
            self.status_label.text = f"Error selecting inventory: {str(e)}"
    
    def run_playbook(self, widget):
        """Run the specified Ansible playbook"""
        # Reset the output display
        self.output_view.value = ""
        self.status_label.text = "Running playbook..."
        
        try:
            playbook = self.playbook_path.value
            inventory = self.inventory_path.value
            
            if not playbook:
                self.status_label.text = "Error: Please select a playbook"
                return
                
            # Import ansible_runner here to avoid startup delays
            # and potential issues on platforms where it might not be available
            import ansible_runner
            
            # Run in a background thread to keep the UI responsive
            def run_in_background():
                try:
                    r = ansible_runner.run(
                        playbook=playbook,
                        inventory=inventory if inventory else None,
                        quiet=False,
                        json_mode=True
                    )
                    
                    output = f"Playbook completed with status: {r.status}\n"
                    output += f"Final return code: {r.rc}\n\n"
                    
                    # Show event output
                    if r.events:
                        output += "Events:\n"
                        for event in r.events:
                            if event['event'] == 'runner_on_ok':
                                task_name = event.get('event_data', {}).get('task', '')
                                host = event.get('event_data', {}).get('host', '')
                                if 'res' in event.get('event_data', {}):
                                    if 'msg' in event['event_data']['res']:
                                        msg = event['event_data']['res']['msg']
                                        output += f"✓ {host}: {task_name} - {msg}\n"
                                    else:
                                        output += f"✓ {host}: {task_name}\n"
                            elif event['event'] == 'runner_on_failed':
                                task_name = event.get('event_data', {}).get('task', '')
                                host = event.get('event_data', {}).get('host', '')
                                output += f"✗ {host}: {task_name} - FAILED\n"
                    
                    # Update UI in the main thread
                    def update_ui():
                        self.output_view.value = output
                        self.status_label.text = "Completed" if r.rc == 0 else "Failed"
                    
                    self.add_background_task(update_ui)
                    
                except Exception as e:
                    def update_error():
                        self.output_view.value = f"Error: {str(e)}"
                        self.status_label.text = "Error"
                    
                    self.add_background_task(update_error)
            
            self.add_background_task(run_in_background)
            
        except ImportError:
            self.output_view.value = (
                "Error: ansible_runner module not available.\n"
                "This may not be supported on your current platform."
            )
            self.status_label.text = "Error: Missing dependencies"
        except Exception as e:
            self.output_view.value = f"Error: {str(e)}"
            self.status_label.text = "Error"


def main():
    return briefcase_ansible_test()
