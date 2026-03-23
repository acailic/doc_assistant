"""Tests for answer generator."""

import os
from pathlib import Path

import pytest

from doc_assistant.answerer.core import MIN_RELEVANCE_THRESHOLD, AnswerGenerator
from doc_assistant.models import Chunk


def test_answer_generator_low_score_returns_early():
    """Test that low relevance scores return early without API call.

    This test doesn't require an API key since it should return before
    making any API calls.
    """
    generator = AnswerGenerator()

    # Chunks with low relevance scores
    low_score_chunks = [
        Chunk(
            content="Some unrelated content about apples.",
            source=Path("fruit.md"),
            chunk_index=0,
            metadata={"score": 0.1},
        ),
        Chunk(
            content="More unrelated content about oranges.",
            source=Path("fruit.md"),
            chunk_index=1,
            metadata={"score": 0.15},
        ),
    ]

    answer = generator.generate("How do I configure authentication?", low_score_chunks)

    # Should return early without calling API
    assert "couldn't find" in answer.content.lower() or "relevant" in answer.content.lower()
    assert answer.confidence < MIN_RELEVANCE_THRESHOLD
    assert len(answer.sources) == 0


def test_answer_generator_filters_low_score_chunks():
    """Test that chunks below threshold are filtered from context.

    This test doesn't require an API key since the filtered result has no chunks.
    """
    generator = AnswerGenerator()

    # Mix of high and low scores, but all below chunk threshold
    mixed_chunks = [
        Chunk(
            content="Low relevance content.",
            source=Path("doc1.md"),
            chunk_index=0,
            metadata={"score": 0.1},
        ),
        Chunk(
            content="Also low relevance.",
            source=Path("doc2.md"),
            chunk_index=0,
            metadata={"score": 0.15},
        ),
    ]

    answer = generator.generate("What is this about?", mixed_chunks)

    # Should return early since all chunks filtered
    assert answer.confidence < MIN_RELEVANCE_THRESHOLD


def test_answer_generator_confidence_reflects_scores():
    """Test that confidence score reflects actual retrieval scores.

    Requires valid ANTHROPIC_API_KEY to run.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")

    generator = AnswerGenerator()

    chunks = [
        Chunk(
            content="To configure authentication, edit the auth.yaml file and add your credentials.",
            source=Path("auth.md"),
            chunk_index=0,
            metadata={"score": 0.85},
        ),
    ]

    answer = generator.generate("How do I configure authentication?", chunks)

    # Check if the answer indicates auth failure (API catches errors internally)
    if answer.confidence == 0.0 and (
        "authentication" in answer.content.lower()
        or "api key" in answer.content.lower()
        or "failed to connect" in answer.content.lower()
        or "api error" in answer.content.lower()
    ):
        pytest.skip("No valid API key available")

    # Confidence should be the average score (0.85 in this case)
    assert 0.7 <= answer.confidence <= 1.0


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
def test_answer_generator_creates_answer():
    """Test that answer generator creates an answer from chunks."""
    generator = AnswerGenerator()

    chunks = [
        Chunk(
            content="To configure authentication, edit the auth.yaml file and add your credentials.",
            source=Path("auth.md"),
            chunk_index=0,
            metadata={"score": 0.8},
        ),
    ]

    answer = generator.generate("How do I configure authentication?", chunks)

    # Check if the answer indicates auth failure (API catches errors internally)
    if answer.confidence == 0.0 and (
        "authentication" in answer.content.lower()
        or "api key" in answer.content.lower()
        or "failed to connect" in answer.content.lower()
        or "api error" in answer.content.lower()
    ):
        pytest.skip("No valid API key available")

    assert answer.content
    assert len(answer.content) > 0
    assert Path("auth.md") in answer.sources


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
def test_answer_generator_includes_sources():
    """Test that answer includes source citations."""
    generator = AnswerGenerator()

    chunks = [
        Chunk(
            content="API rate limit is 100 requests per minute.",
            source=Path("api.md"),
            chunk_index=0,
            metadata={"score": 0.75},
        ),
        Chunk(
            content="Rate limiting helps prevent abuse.",
            source=Path("security.md"),
            chunk_index=0,
            metadata={"score": 0.72},
        ),
    ]

    answer = generator.generate("What is the rate limit?", chunks)

    # Check if the answer indicates auth failure (API catches errors internally)
    if answer.confidence == 0.0 and (
        "authentication" in answer.content.lower()
        or "api key" in answer.content.lower()
        or "failed to connect" in answer.content.lower()
        or "api error" in answer.content.lower()
    ):
        pytest.skip("No valid API key available")

    assert len(answer.sources) >= 1
