"""ChromaDB index management."""

import hashlib
from collections.abc import Sequence
from pathlib import Path

import chromadb
from chromadb.config import Settings

from ..models import Chunk


class IndexManager:
    """Manage ChromaDB vector store for document chunks.

    Uses ChromaDB's default embedding function (all-MiniLM-L6-v2) which
    runs locally without requiring an API key.
    """

    def __init__(
        self,
        persist_dir: Path,
        collection_name: str = "doc_assistant",
    ):
        """Initialize index manager.

        Args:
            persist_dir: Directory to store ChromaDB data
            collection_name: Name of the collection to use
        """
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )

        # Get or create collection (ChromaDB auto-embeds with default function)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: Sequence[Chunk]) -> None:
        """Add chunks to the vector store.

        ChromaDB will automatically generate embeddings using its default
        embedding function (all-MiniLM-L6-v2).

        Args:
            chunks: Sequence of Chunk objects to add
        """
        if not chunks:
            return

        # Generate unique IDs for each chunk
        ids = [self._generate_chunk_id(chunk) for chunk in chunks]

        # Prepare data for ChromaDB
        documents = [chunk.content for chunk in chunks]
        metadatas = [
            {
                "source": str(chunk.source),
                "chunk_index": chunk.chunk_index,
                **chunk.metadata,
            }
            for chunk in chunks
        ]

        # Add to collection - ChromaDB auto-embeds with default function
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,  # type: ignore[arg-type]
        )

    def count(self) -> int:
        """Get the number of documents in the collection."""
        return self.collection.count()

    def clear(self) -> None:
        """Clear all documents from the collection."""
        # Delete and recreate collection
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_chunks(self, chunks: Sequence[Chunk]) -> None:
        """Add or update chunks in the vector store.

        Uses upsert to handle both new and existing chunks efficiently.
        ChromaDB will automatically generate embeddings.

        Args:
            chunks: Sequence of Chunk objects to add or update
        """
        if not chunks:
            return

        # Generate unique IDs for each chunk
        ids = [self._generate_chunk_id(chunk) for chunk in chunks]

        # Prepare data for ChromaDB
        documents = [chunk.content for chunk in chunks]
        metadatas = [
            {
                "source": str(chunk.source),
                "chunk_index": chunk.chunk_index,
                **chunk.metadata,
            }
            for chunk in chunks
        ]

        # Upsert to collection - ChromaDB auto-embeds with default function
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,  # type: ignore[arg-type]
        )

    def get_indexed_sources(self) -> dict[str, str]:
        """Get mapping of source paths to content hashes.

        Returns:
            Dictionary mapping source path to content hash for all indexed documents
        """
        result: dict[str, str] = {}
        if self.collection.count() == 0:
            return result

        # Get all documents with metadata
        all_items = self.collection.get(include=["metadatas"])

        if all_items["metadatas"]:
            for metadata in all_items["metadatas"]:
                source = metadata.get("source", "")
                content_hash = metadata.get("content_hash", "")
                if source and content_hash:
                    result[str(source)] = str(content_hash)

        return result

    def remove_source(self, source: str) -> None:
        """Remove all chunks for a given source.

        Args:
            source: Source path to remove
        """
        self.collection.delete(where={"source": source})

    def _generate_chunk_id(self, chunk: Chunk) -> str:
        """Generate a stable ID for a chunk based on source and index.

        Uses source path and chunk index to create a stable ID that allows
        upsert operations to update existing chunks correctly.
        """
        # Use SHA-256 truncated to 16 hex chars (64 bits) to minimize collision risk
        source_hash = hashlib.sha256(str(chunk.source).encode()).hexdigest()[:16]
        return f"{source_hash}_{chunk.chunk_index}"
