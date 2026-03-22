"""Tests for retriever."""

import tempfile
from pathlib import Path

import pytest

from doc_assistant.indexer.core import IndexManager
from doc_assistant.models import Chunk
from doc_assistant.retriever.core import Retriever


@pytest.fixture
def populated_index():
    """Create an index with test chunks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = IndexManager(persist_dir=Path(tmpdir))

        chunks = [
            Chunk(
                content="Authentication is configured via the auth.yaml file.",
                source=Path("auth.md"),
                chunk_index=0,
                metadata={"format": "md"},
            ),
            Chunk(
                content="Database settings are in config/database.yml.",
                source=Path("config.md"),
                chunk_index=0,
                metadata={"format": "md"},
            ),
            Chunk(
                content="API keys should be stored in environment variables.",
                source=Path("security.md"),
                chunk_index=0,
                metadata={"format": "md"},
            ),
        ]

        manager.add_chunks(chunks)
        yield manager


def test_retriever_finds_relevant_chunks(populated_index):
    """Test that retriever finds relevant chunks for a query."""
    retriever = Retriever(index_manager=populated_index)

    results = retriever.retrieve("How do I configure authentication?", top_k=2)

    assert len(results) >= 1
    # Should find the auth.md content
    assert any("auth" in str(r.source).lower() for r in results)


def test_retriever_respects_top_k(populated_index):
    """Test that retriever respects top_k parameter."""
    retriever = Retriever(index_manager=populated_index)

    results = retriever.retrieve("configuration", top_k=1)
    assert len(results) <= 1


def test_retriever_includes_scores(populated_index):
    """Test that retriever includes similarity scores."""
    retriever = Retriever(index_manager=populated_index)

    results = retriever.retrieve("authentication", top_k=2)

    # All results should have metadata including score
    for result in results:
        assert result.metadata.get("score") is not None
