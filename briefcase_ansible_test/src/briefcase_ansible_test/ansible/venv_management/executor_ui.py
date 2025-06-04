"""
UI integration for venv_management executor functions.

This module bridges the gap between the pure business logic in executor.py
and UI concerns, providing callback-aware wrappers and UI formatting.
"""

from typing import Dict, Any, Optional, List, Callable
from .executor import run_playbook_with_venv, VenvExecutionResult
from .ui import format_success_message, format_error_message
from ..callbacks import SimpleCallback


def run_playbook_with_venv_ui(
    venv_wrapper_playbook_path: str,
    inventory_path: str,
    ssh_key_path: str,
    metadata_dir_path: str,
    playbook_path: str,
    ui_updater,
    target_host: str = "night2.lan",
    persist: bool = False,
    venv_name: Optional[str] = None,
    collections: Optional[List[str]] = None,
    python_packages: Optional[List[str]] = None,
    extra_vars: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    UI-aware wrapper for run_playbook_with_venv.
    
    This function handles UI updates and callbacks while delegating
    the core execution logic to the pure business logic function.
    
    Returns True if successful, False otherwise (for backwards compatibility).
    """
    try:
        # Call the pure business logic function
        result = run_playbook_with_venv(
            venv_wrapper_playbook_path=venv_wrapper_playbook_path,
            inventory_path=inventory_path,
            ssh_key_path=ssh_key_path,
            metadata_dir_path=metadata_dir_path,
            playbook_path=playbook_path,
            target_host=target_host,
            persist=persist,
            venv_name=venv_name,
            collections=collections,
            python_packages=python_packages,
            extra_vars=extra_vars,
        )
        
        # Update UI with messages from execution
        for message in result.messages:
            ui_updater.add_text_to_output(f"{message}\n")
        
        # Update UI based on success/failure
        if result.success:
            success_msg = format_success_message(
                "Virtual environment playbook execution",
                f"venv '{result.venv_name}'"
            )
            ui_updater.add_text_to_output(f"{success_msg}\n")
        else:
            error_msg = format_error_message(
                "Virtual environment playbook execution",
                Exception(f"Failed with return code {result.result_code}")
            )
            ui_updater.add_text_to_output(f"{error_msg}\n")
        
        return result.success
        
    except Exception as e:
        # Handle any unexpected errors
        error_msg = format_error_message("Virtual environment playbook execution", e)
        ui_updater.add_text_to_output(f"{error_msg}\n")
        return False


def create_ansible_callback_for_ui(ui_updater) -> SimpleCallback:
    """
    Create an Ansible callback that integrates with the UI updater.
    
    This function encapsulates the UI callback creation logic,
    making it reusable across different execution contexts.
    """
    return SimpleCallback(ui_updater)


def run_playbook_with_venv_ui_advanced(
    venv_wrapper_playbook_path: str,
    inventory_path: str,
    ssh_key_path: str,
    metadata_dir_path: str,
    playbook_path: str,
    ui_updater,
    progress_callback: Optional[Callable[[str], None]] = None,
    target_host: str = "night2.lan",
    persist: bool = False,
    venv_name: Optional[str] = None,
    collections: Optional[List[str]] = None,
    python_packages: Optional[List[str]] = None,
    extra_vars: Optional[Dict[str, Any]] = None,
) -> VenvExecutionResult:
    """
    Advanced UI-aware wrapper that returns full result details.
    
    This version provides more detailed feedback and progress updates,
    useful for more sophisticated UI integrations.
    
    Returns the full result dictionary from the core execution function.
    """
    try:
        # Notify progress if callback provided
        if progress_callback:
            progress_callback("Starting virtual environment playbook execution...")
        
        # Initial UI update
        ui_updater.add_text_to_output("🚀 Starting venv-based playbook execution...\n")
        
        # Call the pure business logic function
        result = run_playbook_with_venv(
            venv_wrapper_playbook_path=venv_wrapper_playbook_path,
            inventory_path=inventory_path,
            ssh_key_path=ssh_key_path,
            metadata_dir_path=metadata_dir_path,
            playbook_path=playbook_path,
            target_host=target_host,
            persist=persist,
            venv_name=venv_name,
            collections=collections,
            python_packages=python_packages,
            extra_vars=extra_vars,
        )
        
        # Progress update
        if progress_callback:
            status = "completed successfully" if result.success else "failed"
            progress_callback(f"Execution {status}")
        
        # Detailed UI updates
        for message in result.messages:
            ui_updater.add_text_to_output(f"📋 {message}\n")
        
        if result.success:
            ui_updater.add_text_to_output(f"✅ Successfully executed playbook in venv '{result.venv_name}'\n")
        else:
            ui_updater.add_text_to_output(f"❌ Execution failed with return code {result.result_code}\n")
        
        return result
        
    except Exception as e:
        error_msg = format_error_message("Virtual environment playbook execution", e)
        ui_updater.add_text_to_output(f"{error_msg}\n")
        
        if progress_callback:
            progress_callback("Execution failed with error")
        
        return VenvExecutionResult(
            success=False,
            result_code=-1,
            venv_metadata=None,
            messages=[str(e)],
            venv_name=venv_name or "unknown",
            existing_metadata=None,
            error=str(e)
        )