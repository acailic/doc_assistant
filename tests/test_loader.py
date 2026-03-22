"""Tests for document loader."""

from pathlib import Path

import pytest

from doc_assistant.loader.core import DocumentLoader

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_loader_discovers_markdown_files():
    """Test that loader finds markdown files."""
    loader = DocumentLoader(FIXTURES_DIR)
    docs = list(loader.load())

    markdown_docs = [d for d in docs if d.source.suffix == ".md"]
    assert len(markdown_docs) >= 1
    assert any("Sample Document" in d.content for d in markdown_docs)


def test_loader_discovers_python_files():
    """Test that loader finds Python files."""
    loader = DocumentLoader(FIXTURES_DIR)
    docs = list(loader.load())

    python_docs = [d for d in docs if d.source.suffix == ".py"]
    assert len(python_docs) >= 1
    assert any("hello" in d.content for d in python_docs)


def test_loader_extracts_metadata():
    """Test that loader extracts file metadata."""
    loader = DocumentLoader(FIXTURES_DIR)
    docs = list(loader.load())

    assert all(d.metadata.get("format") for d in docs)
    assert all(d.metadata.get("modified_time") for d in docs)


def test_loader_handles_nonexistent_directory():
    """Test that loader raises error for nonexistent directory."""
    with pytest.raises(FileNotFoundError):
        DocumentLoader(Path("/nonexistent/path"))


def test_loader_handles_empty_directory(tmp_path):
    """Test that loader returns empty list for empty directory."""
    loader = DocumentLoader(tmp_path)
    docs = list(loader.load())
    assert docs == []


def test_loader_includes_content_hash():
    """Test that loaded documents include content_hash in metadata."""
    loader = DocumentLoader(FIXTURES_DIR)
    docs = list(loader.load())

    assert len(docs) >= 1
    for doc in docs:
        assert "content_hash" in doc.metadata
        # Hash should be a 64-character hex string (SHA-256)
        assert len(doc.metadata["content_hash"]) == 64
        assert all(c in "0123456789abcdef" for c in doc.metadata["content_hash"])


def test_loader_content_hash_is_deterministic():
    """Test that content_hash is consistent for the same content."""
    loader = DocumentLoader(FIXTURES_DIR)
    docs1 = list(loader.load())
    docs2 = list(loader.load())

    # Sort by source for comparison
    docs1 = sorted(docs1, key=lambda d: str(d.source))
    docs2 = sorted(docs2, key=lambda d: str(d.source))

    for d1, d2 in zip(docs1, docs2):
        assert d1.metadata["content_hash"] == d2.metadata["content_hash"]
