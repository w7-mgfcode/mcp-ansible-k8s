"""Utility functions for file management and bundling."""

import re
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

from pydantic import BaseModel


class PlaybookMetadata(BaseModel):
    """
    Metadata for saved playbooks.

    Attributes:
        filename: Playbook filename
        created_at: Creation timestamp
        description: Human-readable description
        size_bytes: File size in bytes
    """

    filename: str
    created_at: datetime
    description: str
    size_bytes: int


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal attacks.

    Args:
        filename: Raw filename from user input

    Returns:
        Sanitized filename safe for filesystem operations
    """
    # Remove any path separators and dangerous characters
    filename = re.sub(r"[^\w\s-]", "", filename)
    filename = filename.replace(" ", "_")
    # Limit length to prevent filesystem issues
    return filename[:100]


def save_playbook(yaml_content: str, description: str, data_dir: Path) -> Path:
    """
    Save playbook to persistent storage.

    Args:
        yaml_content: YAML content to save
        description: Human-readable description for filename
        data_dir: Base data directory path

    Returns:
        Path to saved playbook file
    """
    # Create playbooks directory if it doesn't exist
    playbooks_dir = data_dir / "playbooks"
    playbooks_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_desc = sanitize_filename(description)
    filename = f"{timestamp}_{safe_desc}.yml"

    filepath = playbooks_dir / filename
    filepath.write_text(yaml_content, encoding="utf-8")

    return filepath


def list_saved_playbooks(data_dir: Path) -> list[PlaybookMetadata]:
    """
    List all saved playbooks with metadata.

    Args:
        data_dir: Base data directory path

    Returns:
        List of playbook metadata, sorted by creation time (newest first)
    """
    playbooks_dir = data_dir / "playbooks"

    if not playbooks_dir.exists():
        return []

    playbooks: list[PlaybookMetadata] = []
    for filepath in sorted(playbooks_dir.glob("*.yml"), reverse=True):
        stat = filepath.stat()

        # Extract description from filename (remove timestamp prefix)
        parts = filepath.stem.split("_", 2)
        description = parts[-1] if len(parts) >= 3 else filepath.stem

        playbooks.append(
            PlaybookMetadata(
                filename=filepath.name,
                created_at=datetime.fromtimestamp(stat.st_mtime),
                description=description.replace("_", " "),
                size_bytes=stat.st_size,
            )
        )

    return playbooks


def load_playbook(filename: str, data_dir: Path) -> str:
    """
    Load playbook content from storage.

    Args:
        filename: Playbook filename to load
        data_dir: Base data directory path

    Returns:
        Playbook YAML content

    Raises:
        FileNotFoundError: If playbook doesn't exist
        ValueError: If filename contains path traversal attempts
    """
    # Validate filename to prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise ValueError(f"Invalid filename (contains path separators): {filename}")

    filepath = data_dir / "playbooks" / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Playbook not found: {filename}")

    # Verify resolved path is still within playbooks directory (defense in depth)
    try:
        filepath.resolve().relative_to((data_dir / "playbooks").resolve())
    except ValueError:
        raise ValueError(f"Path traversal detected: {filename}")

    return filepath.read_text(encoding="utf-8")


def delete_playbook(filename: str, data_dir: Path) -> bool:
    """
    Delete a saved playbook.

    Args:
        filename: Playbook filename to delete
        data_dir: Base data directory path

    Returns:
        True if deleted successfully, False if file didn't exist

    Raises:
        ValueError: If filename contains path traversal attempts
    """
    # Validate filename to prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise ValueError(f"Invalid filename (contains path separators): {filename}")

    filepath = data_dir / "playbooks" / filename

    # Verify resolved path is still within playbooks directory
    try:
        filepath.resolve().relative_to((data_dir / "playbooks").resolve())
    except ValueError:
        raise ValueError(f"Path traversal detected: {filename}")

    if filepath.exists():
        filepath.unlink()
        return True
    return False


def create_zip_bundle(playbook_yaml: str, readme_md: str, bundle_name: str) -> bytes:
    """
    Create ZIP bundle containing playbook and README.

    Args:
        playbook_yaml: Playbook YAML content
        readme_md: README markdown content
        bundle_name: Base name for the bundle (used in filenames)

    Returns:
        ZIP file content as bytes
    """
    # Reason: Use BytesIO to create ZIP in memory without temp files
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Add playbook
        zip_file.writestr(f"{bundle_name}.yml", playbook_yaml)

        # Add README
        zip_file.writestr("README.md", readme_md)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()
