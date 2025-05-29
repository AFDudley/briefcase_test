"""
Functional utilities for managing virtual environment metadata.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any


def get_metadata_dir(app_paths) -> str:
    """Get the metadata directory path, creating it if needed."""
    metadata_dir = os.path.join(app_paths.app, "resources", "venv_metadata")
    os.makedirs(metadata_dir, exist_ok=True)
    return metadata_dir


def create_metadata_filename(venv_name: str, target_host: str) -> str:
    """Generate a metadata filename from venv name and host."""
    return f"{venv_name}_{target_host}.json"


def create_metadata_filepath(app_paths, venv_name: str, target_host: str) -> str:
    """Generate the full filepath for metadata storage."""
    return os.path.join(
        get_metadata_dir(app_paths),
        create_metadata_filename(venv_name, target_host)
    )


def enrich_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Add app-specific fields to metadata."""
    return {
        **metadata,
        "last_updated": datetime.now().isoformat(),
        "metadata_version": "1.0"
    }


def save_venv_metadata(app_paths, venv_name: str, metadata: Dict[str, Any]) -> str:
    """
    Save virtual environment metadata to JSON file.
    
    Returns the filepath where metadata was saved.
    """
    enriched = enrich_metadata(metadata)
    filepath = create_metadata_filepath(app_paths, venv_name, metadata["target_host"])
    
    with open(filepath, 'w') as f:
        json.dump(enriched, f, indent=2)
    
    # Update the index
    update_venv_index(app_paths, venv_name, enriched)
    
    return filepath


def load_venv_metadata(app_paths, venv_name: str, target_host: str) -> Optional[Dict[str, Any]]:
    """Load metadata for a specific virtual environment."""
    filepath = create_metadata_filepath(app_paths, venv_name, target_host)
    
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return None


def get_index_filepath(app_paths) -> str:
    """Get the path to the venv index file."""
    return os.path.join(get_metadata_dir(app_paths), "venv_index.json")


def load_venv_index(app_paths) -> Dict[str, Dict[str, Any]]:
    """Load the venv index, returning empty dict if not found."""
    index_file = get_index_filepath(app_paths)
    
    if os.path.exists(index_file):
        with open(index_file, 'r') as f:
            return json.load(f).get("venvs", {})
    return {}


def create_index_entry(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Create a summary entry for the venv index."""
    ansible_version = metadata.get("ansible_version", [])
    return {
        "target_host": metadata["target_host"],
        "persistent": metadata["persistent"],
        "created_at": metadata["created_at"],
        "last_updated": metadata["last_updated"],
        "python_version": metadata["python_version"],
        "ansible_version": ansible_version[0] if ansible_version else "unknown"
    }


def update_venv_index(app_paths, venv_name: str, metadata: Dict[str, Any]) -> None:
    """Update the venv index with new or updated entry."""
    index = {"venvs": load_venv_index(app_paths)}
    index["venvs"][venv_name] = create_index_entry(metadata)
    
    with open(get_index_filepath(app_paths), 'w') as f:
        json.dump(index, f, indent=2)


def get_venv_index(app_paths) -> Dict[str, Dict[str, Any]]:
    """Get the current venv index."""
    return load_venv_index(app_paths)


def list_all_venvs(app_paths) -> List[Dict[str, Any]]:
    """
    List all known virtual environments with their metadata.
    
    Returns a list of dicts, each containing venv_name and metadata.
    """
    index = load_venv_index(app_paths)
    return [
        {"venv_name": name, **info}
        for name, info in index.items()
    ]


def filter_persistent_venvs(venvs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter to only persistent virtual environments."""
    return [v for v in venvs if v.get("persistent", False)]


def filter_venvs_by_host(venvs: List[Dict[str, Any]], target_host: str) -> List[Dict[str, Any]]:
    """Filter virtual environments by target host."""
    return [v for v in venvs if v.get("target_host") == target_host]


def sort_venvs_by_date(venvs: List[Dict[str, Any]], newest_first: bool = True) -> List[Dict[str, Any]]:
    """Sort virtual environments by creation date."""
    return sorted(
        venvs,
        key=lambda v: v.get("created_at", ""),
        reverse=newest_first
    )