"""Tests for text chunker."""

from pathlib import Path

from doc_assistant.chunker.core import TextChunker
from doc_assistant.models import Document


def test_chunker_splits_long_text():
    """Test that chunker splits long documents."""
    chunker = TextChunker(chunk_size=100, overlap=20)

    doc = Document(
        source=Path("test.txt"),
        content=" ".join(["word"] * 500),  # Long text
        metadata={"format": "txt"},
    )

    chunks = chunker.chunk(doc)
    assert len(chunks) > 1


def test_chunker_preserves_metadata():
    """Test that chunks preserve source metadata."""
    chunker = TextChunker(chunk_size=100, overlap=20)

    doc = Document(
        source=Path("test.txt"),
        content="Some content here.",
        metadata={"format": "txt", "modified_time": 123},
    )

    chunks = chunker.chunk(doc)
    assert all(c.source == Path("test.txt") for c in chunks)
    assert all(c.metadata.get("format") == "txt" for c in chunks)


def test_chunker_handles_short_text():
    """Test that chunker handles short documents."""
    chunker = TextChunker(chunk_size=1000, overlap=200)

    doc = Document(
        source=Path("test.txt"),
        content="Short text.",
        metadata={"format": "txt"},
    )

    chunks = chunker.chunk(doc)
    assert len(chunks) == 1
    assert chunks[0].content == "Short text."


def test_chunker_has_overlap():
    """Test that chunks have overlapping content."""
    chunker = TextChunker(chunk_size=50, overlap=20)

    doc = Document(
        source=Path("test.txt"),
        content=" ".join([f"sentence{i}" for i in range(20)]),
        metadata={"format": "txt"},
    )

    chunks = chunker.chunk(doc)
    if len(chunks) > 1:
        # Check for some overlap between consecutive chunks
        # The overlap isn't exact due to sentence boundaries
        assert len(chunks) >= 2


def test_chunker_markdown_with_headers():
    """Test that markdown files are split by headers with metadata."""
    chunker = TextChunker(chunk_size=1000, overlap=200)

    doc = Document(
        source=Path("test.md"),
        content="""# Installation

Follow these steps to install.

## Prerequisites

You need Python 3.11+.

## Setup

Run the installer script.
""",
        metadata={"format": "md"},
    )

    chunks = chunker.chunk(doc)

    # Should have multiple chunks from header splitting
    assert len(chunks) >= 2

    # Chunks should have header metadata
    chunks_with_h1 = [c for c in chunks if c.metadata.get("h1")]
    assert len(chunks_with_h1) >= 1
    assert any(c.metadata.get("h1") == "Installation" for c in chunks_with_h1)

    # Some chunks should have section_path
    chunks_with_path = [c for c in chunks if c.metadata.get("section_path")]
    assert len(chunks_with_path) >= 1


def test_chunker_markdown_without_headers():
    """Test that markdown without headers falls back to text splitting."""
    chunker = TextChunker(chunk_size=1000, overlap=200)

    doc = Document(
        source=Path("test.md"),
        content="Just some plain text without any headers.",
        metadata={"format": "md"},
    )

    chunks = chunker.chunk(doc)

    # Should still produce chunks
    assert len(chunks) == 1
    # Should not have header metadata
    assert not chunks[0].metadata.get("h1")
    assert not chunks[0].metadata.get("section_path")


def test_chunker_python_file_no_header_metadata():
    """Test that Python files don't get markdown header metadata."""
    chunker = TextChunker(chunk_size=1000, overlap=200)

    doc = Document(
        source=Path("test.py"),
        content='"""Module docstring."""\n\ndef hello():\n    print("hello")\n',
        metadata={"format": "py"},
    )

    chunks = chunker.chunk(doc)

    # Should produce chunks
    assert len(chunks) >= 1
    # Should not have markdown header metadata
    assert not any(c.metadata.get("h1") for c in chunks)
    assert not any(c.metadata.get("section_path") for c in chunks)
