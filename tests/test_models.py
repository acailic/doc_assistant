"""Tests for Pydantic models."""

from pathlib import Path

from doc_assistant.models import Answer
from doc_assistant.models import Chunk
from doc_assistant.models import Document


def test_document_model():
    """Test Document model creation."""
    doc = Document(
        source=Path("test.md"),
        content="# Test\n\nHello world",
        metadata={"format": "md", "modified_time": 1234567890},
    )
    assert doc.source == Path("test.md")
    assert "Hello world" in doc.content
    assert doc.metadata["format"] == "md"


def test_chunk_model():
    """Test Chunk model creation."""
    chunk = Chunk(
        content="This is a chunk of text",
        source=Path("test.md"),
        chunk_index=0,
        metadata={"format": "md"},
    )
    assert chunk.content == "This is a chunk of text"
    assert chunk.chunk_index == 0


def test_answer_model():
    """Test Answer model creation."""
    answer = Answer(
        content="To configure authentication, edit the config file.",
        sources=[Path("auth.md"), Path("config.md")],
        confidence=0.85,
    )
    assert "configure authentication" in answer.content
    assert len(answer.sources) == 2
