"""Tests for utility functions."""

import zipfile
from io import BytesIO
from pathlib import Path

import pytest

from src.utils import (
    PlaybookMetadata,
    create_zip_bundle,
    delete_playbook,
    list_saved_playbooks,
    load_playbook,
    sanitize_filename,
    save_playbook,
)


def test_sanitize_filename() -> None:
    """Test filename sanitization."""
    # Test basic sanitization (dots are removed for safety)
    assert sanitize_filename("test file.yml") == "test_fileyml"

    # Test dangerous characters removed
    assert sanitize_filename("../../../etc/passwd") == "etcpasswd"
    assert sanitize_filename("file<>:|?*.yml") == "fileyml"

    # Test Windows-style path traversal
    assert sanitize_filename("..\\..\\windows\\system32") == "windowssystem32"

    # Test spaces converted to underscores
    assert sanitize_filename("my test file") == "my_test_file"

    # Test length limit
    long_name = "a" * 200
    result = sanitize_filename(long_name)
    assert len(result) == 100


def test_save_playbook(tmp_path: Path) -> None:
    """Test playbook is saved with correct filename and content."""
    yaml_content = "---\ntest: playbook"
    description = "Test Deployment"

    filepath = save_playbook(yaml_content, description, tmp_path)

    # Verify file exists
    assert filepath.exists()

    # Verify content
    assert filepath.read_text() == yaml_content

    # Verify filename structure (timestamp_description.yml)
    assert "test_deployment" in filepath.name.lower()
    assert filepath.suffix == ".yml"

    # Verify directory created
    assert (tmp_path / "playbooks").exists()


def test_list_saved_playbooks_empty(tmp_path: Path) -> None:
    """Test listing playbooks when directory is empty."""
    playbooks = list_saved_playbooks(tmp_path)
    assert playbooks == []


def test_list_saved_playbooks(tmp_path: Path) -> None:
    """Test listing saved playbooks returns correct metadata."""
    # Create test playbooks
    save_playbook("---\ntest1", "First Playbook", tmp_path)
    save_playbook("---\ntest2", "Second Playbook", tmp_path)

    playbooks = list_saved_playbooks(tmp_path)

    assert len(playbooks) == 2
    assert all(isinstance(p, PlaybookMetadata) for p in playbooks)
    assert all(p.filename.endswith(".yml") for p in playbooks)
    assert all(p.size_bytes > 0 for p in playbooks)

    # Check they're sorted by creation time (newest first)
    assert playbooks[0].created_at >= playbooks[1].created_at


def test_list_saved_playbooks_description_extraction(tmp_path: Path) -> None:
    """Test description extraction from filenames with edge cases."""
    # list_saved_playbooks expects files in {data_dir}/playbooks/
    playbooks_dir = tmp_path / "playbooks"
    playbooks_dir.mkdir(exist_ok=True)

    # Case 1: Filename with only timestamp (no description)
    (playbooks_dir / "20231201_120000.yml").write_text("---\ntest")

    # Case 2: Description with multiple underscores
    (playbooks_dir / "20231201_120100_my_complex_deployment_name.yml").write_text("---\ntest")

    playbooks = list_saved_playbooks(tmp_path)

    # Verify both files are listed
    assert len(playbooks) == 2

    # Find the files by searching descriptions
    no_desc = next(p for p in playbooks if "20231201_120000" in p.filename)
    multi_underscore = next(p for p in playbooks if "my_complex" in p.filename)

    # Case 1: No description fallback (last part after splitting)
    assert len(no_desc.description) > 0

    # Case 2: Multiple underscores should be preserved in description
    assert "my complex deployment name" in multi_underscore.description


def test_load_playbook(tmp_path: Path) -> None:
    """Test loading playbook returns correct content."""
    yaml_content = "---\ntest: playbook"
    filepath = save_playbook(yaml_content, "Test", tmp_path)

    loaded_content = load_playbook(filepath.name, tmp_path)

    assert loaded_content == yaml_content


def test_load_playbook_not_found(tmp_path: Path) -> None:
    """Test loading non-existent playbook raises error."""
    with pytest.raises(FileNotFoundError, match="Playbook not found"):
        load_playbook("nonexistent.yml", tmp_path)


def test_load_playbook_path_traversal(tmp_path: Path) -> None:
    """Test loading playbook prevents directory traversal."""
    # Test various path traversal attempts
    with pytest.raises(ValueError, match="path separators"):
        load_playbook("../../../etc/passwd", tmp_path)

    with pytest.raises(ValueError, match="path separators"):
        load_playbook("subdir/file.yml", tmp_path)

    with pytest.raises(ValueError, match="path separators"):
        load_playbook("..\\..\\windows\\system32", tmp_path)


def test_delete_playbook(tmp_path: Path) -> None:
    """Test deleting playbook removes file."""
    filepath = save_playbook("---\ntest", "Test", tmp_path)

    # Verify file exists
    assert filepath.exists()

    # Delete
    result = delete_playbook(filepath.name, tmp_path)

    assert result is True
    assert not filepath.exists()


def test_delete_playbook_not_found(tmp_path: Path) -> None:
    """Test deleting non-existent playbook returns False."""
    result = delete_playbook("nonexistent.yml", tmp_path)
    assert result is False


def test_delete_playbook_path_traversal(tmp_path: Path) -> None:
    """Test deleting playbook prevents directory traversal."""
    # Test various path traversal attempts
    with pytest.raises(ValueError, match="path separators"):
        delete_playbook("../../../etc/passwd", tmp_path)

    with pytest.raises(ValueError, match="path separators"):
        delete_playbook("subdir/file.yml", tmp_path)


def test_create_zip_bundle() -> None:
    """Test ZIP bundle creation contains both files."""
    playbook = "---\ntest: playbook"
    readme = "# README\nTest documentation"

    zip_bytes = create_zip_bundle(playbook, readme, "test-bundle")

    # Verify ZIP is valid
    assert isinstance(zip_bytes, bytes)
    assert len(zip_bytes) > 0

    # Verify ZIP contents
    with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
        filenames = zf.namelist()

        assert "test-bundle.yml" in filenames
        assert "README.md" in filenames

        # Verify content
        assert zf.read("test-bundle.yml").decode() == playbook
        assert zf.read("README.md").decode() == readme


def test_create_zip_bundle_compression() -> None:
    """Test ZIP bundle uses compression."""
    playbook = "---\n" + "test: data\n" * 100  # Repetitive content compresses well
    readme = "# README\n" + "content\n" * 100

    zip_bytes = create_zip_bundle(playbook, readme, "compressed")

    # ZIP should be smaller than raw content
    raw_size = len(playbook) + len(readme)
    assert len(zip_bytes) < raw_size
