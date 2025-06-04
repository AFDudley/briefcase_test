"""
Functional utilities for managing virtual environment metadata.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any


def save_venv_metadata(app_paths, venv_name: str, metadata: Dict[str, Any]) -> str:
    """
    Save virtual environment metadata to JSON file.
    
    Returns the filepath where metadata was saved.
    """
    # Create metadata directory if needed
    metadata_dir = os.path.join(app_paths.app, "resources", "venv_metadata")
    os.makedirs(metadata_dir, exist_ok=True)
    
    # Add timestamp and version
    enriched = {
        **metadata,
        "last_updated": datetime.now().isoformat(),
        "metadata_version": "1.0"
    }
    
    # Save to file
    filename = f"{venv_name}_{metadata['target_host']}.json"
    filepath = os.path.join(metadata_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(enriched, f, indent=2)
    
    return filepath


def load_venv_metadata(app_paths, venv_name: str, target_host: str) -> Optional[Dict[str, Any]]:
    """Load metadata for a specific virtual environment."""
    metadata_dir = os.path.join(app_paths.app, "resources", "venv_metadata")
    filename = f"{venv_name}_{target_host}.json"
    filepath = os.path.join(metadata_dir, filename)
    
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return None


def list_all_venvs(app_paths) -> List[Dict[str, Any]]:
    """
    List all known virtual environments by scanning metadata files.
    
    Returns a list of metadata dicts.
    """
    metadata_dir = os.path.join(app_paths.app, "resources", "venv_metadata")
    
    if not os.path.exists(metadata_dir):
        return []
    
    venvs = []
    for filename in os.listdir(metadata_dir):
        if filename.endswith('.json') and '_' in filename:
            filepath = os.path.join(metadata_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    metadata = json.load(f)
                    venvs.append(metadata)
            except (json.JSONDecodeError, IOError):
                # Skip corrupted files
                pass
    
    return venvs


def delete_venv_metadata(app_paths, venv_name: str, target_host: str) -> bool:
    """
    Delete metadata for a virtual environment.
    
    Returns True if deleted, False if not found.
    """
    metadata_dir = os.path.join(app_paths.app, "resources", "venv_metadata")
    filename = f"{venv_name}_{target_host}.json"
    filepath = os.path.join(metadata_dir, filename)
    
    if os.path.exists(filepath):
        os.unlink(filepath)
        return True
    return False