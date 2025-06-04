"""
Functional utilities for formatting venv information for UI display.
"""

from typing import Dict, Any, List


def format_venv_status_line(venv_info: Dict[str, Any]) -> str:
    """Format a single venv entry for status display."""
    status_icon = "💾" if venv_info.get("persistent", False) else "⏱️"
    status_text = "Persistent" if venv_info.get("persistent", False) else "Temporary"

    return (
        f"{status_icon} {status_text} {venv_info.get('venv_name', 'unknown')} "
        f"@ {venv_info.get('target_host', 'unknown')}"
    )


def format_venv_details(venv_info: Dict[str, Any]) -> List[str]:
    """Format detailed information about a venv."""
    return [
        f"  Created: {venv_info.get('created_at', 'unknown')}",
        f"  Python: {venv_info.get('python_version', 'unknown')}",
        f"  Ansible: {venv_info.get('ansible_version', 'unknown')}",
    ]


def format_venv_entry(venv_info: Dict[str, Any]) -> str:
    """Format a complete venv entry with status and details."""
    lines = [format_venv_status_line(venv_info)]
    lines.extend(format_venv_details(venv_info))
    return "\n".join(lines)


def format_venv_list(
    venvs: List[Dict[str, Any]], title: str = "📦 Virtual Environments:"
) -> str:
    """
    Format a list of virtual environments for display.

    Returns formatted string ready for UI output.
    """
    if not venvs:
        return f"{title}\nNo virtual environments found."

    sections = [title, "-" * 50]

    for venv in venvs:
        sections.append("")  # Empty line before each entry
        sections.append(format_venv_entry(venv))

    return "\n".join(sections)


def format_metadata_summary(metadata: Dict[str, Any]) -> str:
    """Format a summary of venv metadata."""
    pip_count = len(metadata.get("pip_packages", []))
    collection_count = len(metadata.get("ansible_collections", {}))

    return (
        f"Virtual Environment: {metadata.get('venv_name', 'unknown')}\n"
        f"Path: {metadata.get('venv_path', 'unknown')}\n"
        f"Python packages: {pip_count}\n"
        f"Ansible collections: {collection_count}\n"
    )


def format_package_list(packages: List[str], max_items: int = 10) -> str:
    """Format a list of packages, truncating if needed."""
    if not packages:
        return "  None installed"

    if len(packages) <= max_items:
        return "\n".join(f"  - {pkg}" for pkg in packages)

    formatted = "\n".join(f"  - {pkg}" for pkg in packages[:max_items])
    return f"{formatted}\n  ... and {len(packages) - max_items} more"


def format_collection_dict(collections: Dict[str, str]) -> str:
    """Format ansible collections dict for display."""
    if not collections:
        return "  None installed"

    return "\n".join(f"  - {name}: {version}" for name, version in collections.items())


def format_venv_status(app_paths) -> str:
    """
    Format the status of all known venvs.

    This is a convenience function that loads and formats all venvs.
    """
    from .metadata import list_all_venvs

    venvs = list_all_venvs(app_paths)
    return format_venv_list(venvs)


def format_error_message(operation: str, error: Exception) -> str:
    """Format an error message for UI display."""
    return f"❌ {operation} failed: {str(error)}"


def format_success_message(operation: str, details: str = "") -> str:
    """Format a success message for UI display."""
    base = f"✅ {operation} completed successfully"
    return f"{base}: {details}" if details else base
