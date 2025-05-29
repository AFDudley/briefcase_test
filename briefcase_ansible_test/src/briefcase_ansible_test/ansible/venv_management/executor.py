"""
Functional utilities for executing playbooks with virtual environments.
"""

import os
import time
from typing import Dict, Any, Optional, List
from functools import partial

from ..playbook import run_ansible_playbook as run_playbook_internal
from .metadata import load_venv_metadata, save_venv_metadata


def get_venv_path(venv_name: str, target_host: str, persist: bool = False) -> str:
    """
    Generate the virtual environment path based on persistence setting.
    
    For persistent venvs, uses ~/ansible-venvs/<name>
    For temporary venvs, uses /tmp/ansible-venv-<name>
    """
    if persist:
        return f"~/ansible-venvs/{venv_name}"
    else:
        return f"/tmp/ansible-venv-{venv_name}"


def create_venv_vars(
    venv_name: str,
    target_host: str,
    persist: bool = False,
    collections: Optional[List[str]] = None,
    python_packages: Optional[List[str]] = None,
    playbook_path: Optional[str] = None,
    extra_vars: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create variables dict for venv wrapper playbook.
    
    This is a pure function that generates the configuration needed
    for the venv management playbook.
    """
    venv_path = get_venv_path(venv_name, target_host, persist)
    
    base_vars = {
        "venv_name": venv_name,
        "venv_path": venv_path,
        "persist_venv": persist,
        "target_host": target_host,
        "collect_metadata": True,
        "ansible_collections": collections or [],
        "python_packages": python_packages or ["ansible-core"],
    }
    
    if playbook_path:
        base_vars["playbook_to_run"] = playbook_path
        
    if extra_vars:
        base_vars.update(extra_vars)
        
    return base_vars


def check_venv_exists(app_paths, venv_name: str, target_host: str) -> Optional[Dict[str, Any]]:
    """
    Check if a virtual environment exists by looking up its metadata.
    
    Returns metadata dict if exists, None otherwise.
    """
    return load_venv_metadata(app_paths, venv_name, target_host)


def format_existing_venv_message(metadata: Dict[str, Any]) -> str:
    """Format a message about an existing venv."""
    return (
        f"Using existing venv '{metadata['venv_name']}' "
        f"created at {metadata['created_at']}"
    )


def generate_temp_venv_name() -> str:
    """Generate a unique name for a temporary venv."""
    return f"temp_{int(time.time())}"


def extract_metadata_from_result(result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract venv metadata from playbook execution result."""
    return result.get("venv_metadata") if result.get("success") else None


def run_venv_wrapper_playbook(
    app,
    wrapper_vars: Dict[str, Any],
    ui_updater
) -> Dict[str, Any]:
    """
    Execute the venv wrapper playbook and return results.
    
    This is a thin wrapper around the internal playbook runner
    that knows about the venv wrapper playbook location.
    """
    wrapper_playbook = os.path.join(
        app.paths.app, 
        "ansible", 
        "venv_management", 
        "playbooks", 
        "venv_wrapper.yml"
    )
    
    # Create a custom callback to capture metadata
    class MetadataCapture:
        def __init__(self):
            self.metadata = None
            
        def capture(self, task_name: str, result: Any):
            if task_name == "Return metadata to iOS app":
                self.metadata = result
    
    capture = MetadataCapture()
    
    # Run the playbook
    result = run_playbook_internal(
        app,
        wrapper_playbook,
        extra_vars=wrapper_vars,
        result_callback=capture.capture
    )
    
    return {
        "success": result == 0,
        "venv_metadata": capture.metadata,
        "result_code": result
    }


def run_playbook_with_venv(
    app,
    playbook_path: str,
    target_host: str = "night2.lan",
    persist: bool = False,
    venv_name: Optional[str] = None,
    collections: Optional[List[str]] = None,
    python_packages: Optional[List[str]] = None,
    extra_vars: Optional[Dict[str, Any]] = None,
    ui_updater = None
) -> bool:
    """
    Run a playbook using a virtual environment on the target host.
    
    This is the main entry point for venv-based playbook execution.
    Returns True if successful, False otherwise.
    """
    # Generate venv name if not provided
    actual_venv_name = venv_name or generate_temp_venv_name()
    
    # Check for existing venv if persistent
    if persist and venv_name:
        existing = check_venv_exists(app.paths, actual_venv_name, target_host)
        if existing and ui_updater:
            ui_updater.add_text_to_output(
                format_existing_venv_message(existing) + "\n"
            )
    
    # Create wrapper variables
    wrapper_vars = create_venv_vars(
        venv_name=actual_venv_name,
        target_host=target_host,
        persist=persist,
        collections=collections,
        python_packages=python_packages,
        playbook_path=playbook_path,
        extra_vars=extra_vars
    )
    
    # Execute the wrapper playbook
    result = run_venv_wrapper_playbook(app, wrapper_vars, ui_updater)
    
    # Save metadata if successful
    if result["success"]:
        metadata = extract_metadata_from_result(result)
        if metadata:
            save_venv_metadata(app.paths, actual_venv_name, metadata)
            if ui_updater:
                ui_updater.add_text_to_output(
                    f"✅ Metadata saved for venv '{actual_venv_name}'\n"
                )
    
    return result["success"]


# Convenience functions for common use cases
create_persistent_venv = partial(run_playbook_with_venv, persist=True)
create_temp_venv = partial(run_playbook_with_venv, persist=False)