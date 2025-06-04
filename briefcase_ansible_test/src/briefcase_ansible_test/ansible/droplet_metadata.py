"""
Metadata management for droplet resources.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any


def save_droplet_metadata(
    metadata_dir_path: str, droplet_name: str, metadata: Dict[str, Any]
) -> str:
    """
    Save droplet metadata to JSON file.

    Returns the filepath where metadata was saved.
    """
    # Create metadata directory if needed
    metadata_dir = os.path.join(metadata_dir_path, "resources", "droplet_metadata")
    os.makedirs(metadata_dir, exist_ok=True)

    # Add timestamp and version
    enriched = {
        **metadata,
        "last_updated": datetime.now().isoformat(),
        "metadata_version": "1.0",
    }

    # Save to file
    filename = f"{droplet_name}.json"
    filepath = os.path.join(metadata_dir, filename)

    with open(filepath, "w") as f:
        json.dump(enriched, f, indent=2)

    return filepath


def load_droplet_metadata(
    metadata_dir_path: str, droplet_name: str
) -> Optional[Dict[str, Any]]:
    """Load metadata for a specific droplet."""
    metadata_dir = os.path.join(metadata_dir_path, "resources", "droplet_metadata")
    filename = f"{droplet_name}.json"
    filepath = os.path.join(metadata_dir, filename)

    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return None


def list_all_droplets(metadata_dir_path: str) -> List[Dict[str, Any]]:
    """
    List all known droplets by scanning metadata files.

    Returns a list of metadata dicts.
    """
    metadata_dir = os.path.join(metadata_dir_path, "resources", "droplet_metadata")

    if not os.path.exists(metadata_dir):
        return []

    droplets = []
    for filename in os.listdir(metadata_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(metadata_dir, filename)
            try:
                with open(filepath, "r") as f:
                    metadata = json.load(f)
                    droplets.append(metadata)
            except (json.JSONDecodeError, IOError):
                # Skip corrupted files
                pass

    return droplets


def delete_droplet_metadata(metadata_dir_path: str, droplet_name: str) -> bool:
    """
    Delete metadata for a droplet.

    Returns True if deleted, False if not found.
    """
    metadata_dir = os.path.join(metadata_dir_path, "resources", "droplet_metadata")
    filename = f"{droplet_name}.json"
    filepath = os.path.join(metadata_dir, filename)

    if os.path.exists(filepath):
        os.unlink(filepath)
        return True
    return False
