"""Tests for index manager."""

import tempfile
from pathlib import Path

import pytest

from doc_assistant.indexer.core import IndexManager
from doc_assistant.models import Chunk


def test_index_manager_creates_collection():
    """Test that index manager creates a collection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = IndexManager(persist_dir=Path(tmpdir))
        assert manager.collection is not None


def test_index_manager_adds_chunks():
    """Test that index manager can add chunks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = IndexManager(persist_dir=Path(tmpdir))

        chunks = [
            Chunk(
                content="First chunk of content",
                source=Path("test.md"),
                chunk_index=0,
                metadata={"format": "md"},
            ),
            Chunk(
                content="Second chunk of content",
                source=Path("test.md"),
                chunk_index=1,
                metadata={"format": "md"},
            ),
        ]

        manager.add_chunks(chunks)

        # Check that chunks were added
        count = manager.count()
        assert count == 2


def test_index_manager_clears_collection():
    """Test that index manager can clear the collection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = IndexManager(persist_dir=Path(tmpdir))

        chunks = [
            Chunk(
                content="Some content",
                source=Path("test.md"),
                chunk_index=0,
                metadata={},
            ),
        ]

        manager.add_chunks(chunks)
        assert manager.count() == 1

        manager.clear()
        assert manager.count() == 0


def test_index_manager_persists_data():
    """Test that index persists between sessions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        persist_path = Path(tmpdir)

        # First session: add chunks
        manager1 = IndexManager(persist_dir=persist_path)
        chunks = [
            Chunk(
                content="Persistent content",
                source=Path("test.md"),
                chunk_index=0,
                metadata={},
            ),
        ]
        manager1.add_chunks(chunks)

        # Second session: check persistence
        manager2 = IndexManager(persist_dir=persist_path)
        assert manager2.count() == 1


def test_index_manager_upsert_chunks():
    """Test that upsert_chunks updates existing chunks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = IndexManager(persist_dir=Path(tmpdir))

        # Add initial chunks
        chunks = [
            Chunk(
                content="Original content",
                source=Path("test.md"),
                chunk_index=0,
                metadata={"content_hash": "abc123"},
            ),
        ]
        manager.add_chunks(chunks)
        assert manager.count() == 1

        # Upsert with updated content
        updated_chunks = [
            Chunk(
                content="Updated content",
                source=Path("test.md"),
                chunk_index=0,
                metadata={"content_hash": "def456"},
            ),
        ]
        manager.upsert_chunks(updated_chunks)

        # Count should still be 1 (updated, not added)
        assert manager.count() == 1


def test_index_manager_get_indexed_sources():
    """Test that get_indexed_sources returns correct mapping."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = IndexManager(persist_dir=Path(tmpdir))

        chunks = [
            Chunk(
                content="Content for file one",
                source=Path("file1.md"),
                chunk_index=0,
                metadata={"content_hash": "hash1"},
            ),
            Chunk(
                content="Content for file two",
                source=Path("file2.md"),
                chunk_index=0,
                metadata={"content_hash": "hash2"},
            ),
        ]
        manager.add_chunks(chunks)

        sources = manager.get_indexed_sources()
        assert len(sources) == 2
        assert "file1.md" in sources
        assert "file2.md" in sources
        assert sources["file1.md"] == "hash1"
        assert sources["file2.md"] == "hash2"


def test_index_manager_remove_source():
    """Test that remove_source deletes chunks for a source."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = IndexManager(persist_dir=Path(tmpdir))

        chunks = [
            Chunk(
                content="Content for file one",
                source=Path("file1.md"),
                chunk_index=0,
                metadata={"content_hash": "hash1"},
            ),
            Chunk(
                content="Content for file two",
                source=Path("file2.md"),
                chunk_index=0,
                metadata={"content_hash": "hash2"},
            ),
        ]
        manager.add_chunks(chunks)
        assert manager.count() == 2

        # Remove file1
        manager.remove_source("file1.md")

        assert manager.count() == 1
        sources = manager.get_indexed_sources()
        assert "file1.md" not in sources
        assert "file2.md" in sources
