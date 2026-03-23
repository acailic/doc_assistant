"""Vector similarity search for retrieval."""

from pathlib import Path

from ..indexer.core import IndexManager
from ..models import Chunk


class Retriever:
    """Retrieve relevant chunks using vector similarity."""

    def __init__(self, index_manager: IndexManager):
        """Initialize retriever.

        Args:
            index_manager: IndexManager instance for vector search
        """
        self.index_manager = index_manager

    def retrieve(self, query: str, top_k: int = 5) -> list[Chunk]:
        """Retrieve relevant chunks for a query.

        Args:
            query: Natural language query
            top_k: Maximum number of results to return

        Returns:
            List of Chunk objects sorted by relevance
        """
        # Query through IndexManager interface (not directly accessing collection)
        results = self.index_manager.query(query, n_results=top_k)

        # Convert to Chunk objects
        chunks = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0

                # Extract metadata values with proper typing
                source_val = metadata.get("source", "unknown")
                chunk_idx_val = metadata.get("chunk_index", 0)

                chunk = Chunk(
                    content=doc,
                    source=Path(str(source_val)),
                    chunk_index=int(chunk_idx_val) if isinstance(chunk_idx_val, int | float) else 0,
                    metadata={
                        **metadata,
                        "score": 1 - distance,  # Convert distance to similarity
                    },
                )
                chunks.append(chunk)

        return chunks
