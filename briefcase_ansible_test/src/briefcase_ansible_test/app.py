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
        
        # Always assume mobile for iOS
        is_mobile = True
        
        # Create default playbooks directory and sample files
        self.playbooks_dir = os.path.join(self.paths.app, 'playbooks')
        self.inventory_dir = os.path.join(self.paths.app, 'inventory')
        # Create directories if they don't exist
        os.makedirs(self.playbooks_dir, exist_ok=True)
        os.makedirs(self.inventory_dir, exist_ok=True)
        # Create sample files
        self.create_sample_files()
        
        # Create file path displays
        # Playbook section
        playbook_box = toga.Box(style=Pack(direction=COLUMN, margin=5))
        playbook_box.add(toga.Label('Playbook:', style=Pack(margin=(0, 5))))
        self.playbook_path = toga.TextInput(readonly=True, style=Pack(flex=1, width=300))
        playbook_box.add(self.playbook_path)
        
        # Inventory section
        inventory_box = toga.Box(style=Pack(direction=COLUMN, margin=5))
        inventory_box.add(toga.Label('Inventory:', style=Pack(margin=(0, 5))))
        self.inventory_path = toga.TextInput(readonly=True, style=Pack(flex=1, width=300))
        inventory_box.add(self.inventory_path)
        
        # Pre-select sample files
        self.playbook_path.value = os.path.join(self.playbooks_dir, 'sample_playbook.yml')
        self.inventory_path.value = os.path.join(self.inventory_dir, 'sample_inventory.ini')
        
        # Run button (smaller on mobile)
        if is_mobile:
            run_button = toga.Button('Run', on_press=self.run_playbook, style=Pack(margin=5))
        else:
            run_button = toga.Button('Run Playbook', on_press=self.run_playbook, style=Pack(margin=5))
        
        # Status and output
        self.status_label = toga.Label('Ready', style=Pack(margin=5))
        self.output_view = toga.MultilineTextInput(readonly=True, style=Pack(flex=1, margin=5, height=200))
        
        # Set up the main window first to allow proper size detection
        self.main_window = toga.MainWindow(title=self.formal_name)
        
        # Add components to main box - adjust based on mobile vs desktop
        title = 'Ansible' if is_mobile else 'Ansible Runner'
        main_box.add(toga.Label(title, style=Pack(text_align='center', font_size=16 if is_mobile else 18, margin=5)))
        main_box.add(playbook_box)
        main_box.add(inventory_box)
        main_box.add(run_button)
        main_box.add(self.status_label)
        main_box.add(self.output_view)
        
        # Apply content and show window
        self.main_window.content = main_box
        
        # Set a maximum size for mobile
        if is_mobile:
            # Set explicit size to fit in iOS simulator viewport
            self.main_window.size = (380, 600)
            
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
        """Use the sample playbook file"""
        try:
            # Use the sample playbook
            sample_playbook_path = os.path.join(self.playbooks_dir, 'sample_playbook.yml')
            
            # Ensure the sample file exists
            if not os.path.exists(sample_playbook_path):
                self.create_sample_files()
                
            # Set the playbook path
            self.playbook_path.value = sample_playbook_path
            self.status_label.text = "Using sample playbook"
        except Exception as e:
            self.status_label.text = f"Error selecting playbook: {str(e)}"
    
    def find_playbook_files(self):
        """Find all playbook files in the playbooks directory"""
        files = []
        if os.path.exists(self.playbooks_dir):
            for file in os.listdir(self.playbooks_dir):
                if file.endswith('.yml') or file.endswith('.yaml'):
                    files.append(file)
        return files
    
    def find_inventory_files(self):
        """Find all inventory files in the inventory directory"""
        files = []
        if os.path.exists(self.inventory_dir):
            for file in os.listdir(self.inventory_dir):
                if file.endswith('.ini'):
                    files.append(file)
        return files
    
    def close_selection_dialog(self):
        """Close the selection dialog window"""
        if hasattr(self, 'selection_window') and self.selection_window:
            self.selection_window.close()
    
    def handle_playbook_selection(self, filename):
        """Handle playbook selection from dialog"""
        if filename:
            full_path = os.path.join(self.playbooks_dir, filename)
            self.playbook_path.value = full_path
        self.close_selection_dialog()
    
    def on_playbook_selected(self, selection):
        """Handle selection of playbook from dropdown"""
        if selection.value:
            full_path = os.path.join(self.playbooks_dir, selection.value)
            self.playbook_path.value = full_path
    
    def select_inventory(self, widget):
        """Use the sample inventory file"""
        try:
            # Use the sample inventory
            sample_inventory_path = os.path.join(self.inventory_dir, 'sample_inventory.ini')
            
            # Ensure the sample file exists
            if not os.path.exists(sample_inventory_path):
                self.create_sample_files()
                
            # Set the inventory path
            self.inventory_path.value = sample_inventory_path
            self.status_label.text = "Using sample inventory"
        except Exception as e:
            self.status_label.text = f"Error selecting inventory: {str(e)}"
    
    def close_inventory_dialog(self):
        """Close the inventory selection dialog window"""
        if hasattr(self, 'inventory_window') and self.inventory_window:
            self.inventory_window.close()
    
    def handle_inventory_selection(self, filename):
        """Handle inventory selection from dialog"""
        if filename:
            full_path = os.path.join(self.inventory_dir, filename)
            self.inventory_path.value = full_path
        self.close_inventory_dialog()
    
    def on_inventory_selected(self, selection):
        """Handle selection of inventory from dropdown"""
        if selection.value:
            full_path = os.path.join(self.inventory_dir, selection.value)
            self.inventory_path.value = full_path
    
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
