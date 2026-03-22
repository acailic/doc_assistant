"""End-to-end integration tests."""

import os
import tempfile
from pathlib import Path

import pytest

from doc_assistant.answerer.core import AnswerGenerator
from doc_assistant.chunker.core import TextChunker
from doc_assistant.indexer.core import IndexManager
from doc_assistant.loader.core import DocumentLoader
from doc_assistant.retriever.core import Retriever

# Skip if no Anthropic API key (embeddings now run locally)
pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_full_pipeline():
    """Test the complete index → query flow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Step 1: Load documents
        loader = DocumentLoader(FIXTURES_DIR)
        docs = list(loader.load())
        assert len(docs) >= 2  # At least md and py files

        # Step 2: Chunk documents
        chunker = TextChunker(chunk_size=500, overlap=100)
        all_chunks = []
        for doc in docs:
            all_chunks.extend(chunker.chunk(doc))
        assert len(all_chunks) >= 1

        # Step 3: Index chunks
        manager = IndexManager(persist_dir=Path(tmpdir))
        manager.add_chunks(all_chunks)
        assert manager.count() >= 1

        # Step 4: Retrieve relevant chunks
        retriever = Retriever(index_manager=manager)
        chunks = retriever.retrieve("sample document", top_k=3)
        assert len(chunks) >= 1

        # Step 5: Generate answer
        generator = AnswerGenerator()
        answer = generator.generate("What is in the sample document?", chunks)

        assert answer.content
        assert len(answer.content) > 0
        assert len(answer.sources) >= 1
