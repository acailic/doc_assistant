"""Claude API answer generation."""

from collections.abc import Sequence
from pathlib import Path

import anthropic

from ..models import Answer
from ..models import Chunk

# Minimum average relevance score to attempt answer generation
MIN_RELEVANCE_THRESHOLD = 0.3

# Minimum score for individual chunks to be included in context
MIN_CHUNK_SCORE = 0.2

RAG_PROMPT = """You are a helpful documentation assistant. Answer the user's question based on the provided context.

Context from documentation:
{context}

Question: {question}

Instructions:
1. Answer based ONLY on the provided context
2. Cite sources using [filename] notation
3. If the context doesn't contain the answer, say so clearly
4. Be concise but thorough"""


class AnswerGenerator:
    """Generate answers using Claude API."""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        """Initialize answer generator.

        Args:
            model: Claude model to use
        """
        self.client = anthropic.Anthropic()
        self.model = model

    def generate(self, question: str, chunks: Sequence[Chunk]) -> Answer:
        """Generate an answer from retrieved chunks.

        Args:
            question: User's question
            chunks: Retrieved chunks for context

        Returns:
            Answer with content and sources
        """
        if not chunks:
            return Answer(
                content="I don't have any relevant documentation to answer that question. Try indexing more documents or rephrasing your query.",
                sources=[],
                confidence=0.0,
            )

        # Extract relevance scores from chunks
        scores = [c.metadata.get("score", 0.0) for c in chunks]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        # Early return if relevance is too low
        if avg_score < MIN_RELEVANCE_THRESHOLD:
            return Answer(
                content="I couldn't find sufficiently relevant documentation to answer that question. Try rephrasing your query or indexing more documents.",
                sources=[],
                confidence=avg_score,
            )

        # Filter out low-scoring chunks (noise reduction)
        good_chunks = [c for c in chunks if c.metadata.get("score", 0.0) >= MIN_CHUNK_SCORE]

        # If all chunks are filtered out, return low confidence
        if not good_chunks:
            return Answer(
                content="The available documentation doesn't seem directly relevant to your question. Try a more specific query.",
                sources=[],
                confidence=avg_score,
            )

        # Build context from filtered chunks
        context_parts = []
        sources: list[Path] = []

        for chunk in good_chunks:
            context_parts.append(f"[{chunk.source.name}]\n{chunk.content}")
            if chunk.source not in sources:
                sources.append(chunk.source)

        context = "\n\n---\n\n".join(context_parts)

        # Call Claude API with error handling
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": RAG_PROMPT.format(context=context, question=question),
                    }
                ],
            )
        except anthropic.AuthenticationError:
            return Answer(
                content="API authentication failed. Please check your ANTHROPIC_API_KEY environment variable.",
                sources=[],
                confidence=0.0,
            )
        except anthropic.RateLimitError:
            return Answer(
                content="API rate limit exceeded. Please wait a moment and try again.",
                sources=[],
                confidence=0.0,
            )
        except anthropic.APIConnectionError as e:
            return Answer(
                content=f"Failed to connect to API. Please check your network connection. Error: {e}",
                sources=[],
                confidence=0.0,
            )
        except anthropic.APIStatusError as e:
            return Answer(
                content=f"API error occurred: {e.message}. Please try again.",
                sources=[],
                confidence=0.0,
            )

        # Extract answer text from TextBlock
        first_block = response.content[0]
        if first_block.type == "text":
            content = first_block.text
        else:
            content = "Unable to generate answer."

        return Answer(
            content=content,
            sources=sources,
            confidence=avg_score,
        )
