"""ChromaDB index management."""

import hashlib
import json
import logging
from collections.abc import Sequence
from pathlib import Path

import chromadb
from chromadb.config import Settings

from ..models import Chunk

logger = logging.getLogger(__name__)

# Batch size for ChromaDB operations to avoid memory issues with large doc sets
BATCH_SIZE = 500

# Filename for the source hash cache (PERF-1: avoids fetching all chunk metadata)
SOURCE_HASH_CACHE_FILE = "source_hashes.json"


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

        Raises:
            RuntimeError: If ChromaDB data is corrupted (with recovery instructions)
        """
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self._source_hash_cache: dict[str, str] | None = None

        # Initialize ChromaDB client with corruption handling
        try:
            self.client = chromadb.PersistentClient(
                path=str(self.persist_dir),
                settings=Settings(anonymized_telemetry=False),
            )

            # Get or create collection (ChromaDB auto-embeds with default function)
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize ChromaDB at {self.persist_dir}: {e}\n\n"
                "This may be due to corrupted index data. Try deleting the "
                f"'{self.persist_dir}' directory and re-indexing your documents."
            ) from e

    def add_chunks(self, chunks: Sequence[Chunk]) -> None:
        """Add chunks to the vector store.

        ChromaDB will automatically generate embeddings using its default
        embedding function (all-MiniLM-L6-v2).

        PERF-2: Batches chunks in groups of BATCH_SIZE to avoid memory
        issues with large document sets.

        Args:
            chunks: Sequence of Chunk objects to add
        """
        if not chunks:
            return

        # PERF-2: Process in batches to avoid memory issues with large doc sets
        chunks_list = list(chunks)
        for i in range(0, len(chunks_list), BATCH_SIZE):
            batch = chunks_list[i : i + BATCH_SIZE]

            # Generate unique IDs for each chunk in batch
            ids = [self._generate_chunk_id(chunk) for chunk in batch]

            # Prepare data for ChromaDB
            documents = [chunk.content for chunk in batch]
            metadatas = [
                {
                    "source": str(chunk.source),
                    "chunk_index": chunk.chunk_index,
                    **chunk.metadata,
                }
                for chunk in batch
            ]

            # Add to collection - ChromaDB auto-embeds with default function
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,  # type: ignore[arg-type]
            )

        # PERF-1: Update source hash cache after adding chunks
        self._update_source_hash_cache(chunks_list)

    def count(self) -> int:
        """Get the number of documents in the collection."""
        return self.collection.count()

    def clear(self) -> None:
        """Clear all documents from the collection.

        Also clears the source hash cache.
        """
        # Delete and recreate collection
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        # PERF-1: Clear the cache
        self._source_hash_cache = {}
        self._save_source_hash_cache()

    def upsert_chunks(self, chunks: Sequence[Chunk]) -> None:
        """Add or update chunks in the vector store.

        Uses upsert to handle both new and existing chunks efficiently.
        ChromaDB will automatically generate embeddings.

        PERF-2: Batches chunks in groups of BATCH_SIZE to avoid memory
        issues with large document sets.

        Args:
            chunks: Sequence of Chunk objects to add or update
        """
        if not chunks:
            return

        # PERF-2: Process in batches to avoid memory issues with large doc sets
        chunks_list = list(chunks)
        for i in range(0, len(chunks_list), BATCH_SIZE):
            batch = chunks_list[i : i + BATCH_SIZE]

            # Generate unique IDs for each chunk in batch
            ids = [self._generate_chunk_id(chunk) for chunk in batch]

            # Prepare data for ChromaDB
            documents = [chunk.content for chunk in batch]
            metadatas = [
                {
                    "source": str(chunk.source),
                    "chunk_index": chunk.chunk_index,
                    **chunk.metadata,
                }
                for chunk in batch
            ]

            # Upsert to collection - ChromaDB auto-embeds with default function
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,  # type: ignore[arg-type]
            )

        # PERF-1: Update source hash cache after upserting chunks
        self._update_source_hash_cache(chunks_list)

    def get_indexed_sources(self) -> dict[str, str]:
        """Get mapping of source paths to content hashes.

        PERF-1: Uses cached source hashes when available to avoid fetching
        all chunk metadata for large indices.

        Returns:
            Dictionary mapping source path to content hash for all indexed documents
        """
        # PERF-1: Use cache if available, avoid fetching all metadata
        if self._source_hash_cache is None:
            self._source_hash_cache = self._load_source_hash_cache()

        return self._source_hash_cache

    def _load_source_hash_cache(self) -> dict[str, str]:
        """Load source hashes from the JSON sidecar file.

        Returns:
            Dictionary of source path -> content hash
        """
        cache_path = self.persist_dir / SOURCE_HASH_CACHE_FILE
        if cache_path.exists():
            try:
                with open(cache_path) as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        logger.debug(f"Loaded source hash cache with {len(data)} entries")
                        return data
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse source hash cache: {e}")
        return {}

    def _save_source_hash_cache(self) -> None:
        """Save source hashes to the JSON sidecar file."""
        cache_path = self.persist_dir / SOURCE_HASH_CACHE_FILE
        try:
            with open(cache_path, "w") as f:
                json.dump(self._source_hash_cache, f, indent=2)
            logger.debug(f"Saved source hash cache with {len(self._source_hash_cache)} entries")
        except OSError as e:
            logger.warning(f"Failed to save source hash cache: {e}")

    def _update_source_hash_cache(self, chunks: Sequence[Chunk]) -> None:
        """Update the source hash cache after adding/upserting chunks.

        PERF-1: Maintains the cache in avoid fetching all metadata on subsequent calls.

        Args:
            chunks: Sequence of chunks to extract source hashes from
        """
        if self._source_hash_cache is None:
            self._source_hash_cache = self._load_source_hash_cache()

        for chunk in chunks:
            source_key = str(chunk.source)
            content_hash = chunk.metadata.get("content_hash", "")
            if content_hash:
                self._source_hash_cache[source_key] = content_hash

        # Save the updated cache
        self._save_source_hash_cache()

    def remove_source(self, source: str) -> None:
        """Remove all chunks for a given source.

        Also removes the source from the hash cache.

        Args:
            source: Source path to remove
        """
        self.collection.delete(where={"source": source})

        # PERF-1: Also remove from cache
        if self._source_hash_cache is not None and source in self._source_hash_cache:
            del self._source_hash_cache[source]
            self._save_source_hash_cache()

    def query(self, query_text: str, n_results: int = 5) -> dict:
        """Query the vector store for similar documents.

        Args:
            query_text: Natural language query
            n_results: Maximum number of results to return

        Returns:
            ChromaDB query results with documents, metadatas, and distances
        """
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

    def get_stats(self) -> dict:
        """Get comprehensive statistics about the index.

        Returns:
            Dictionary with chunk count, sources, total size, last modified, and model info
        """
        stats: dict = {
            "chunk_count": self.collection.count(),
            "sources": [],
            "total_size_bytes": 0,
            "last_modified": None,
            "embedding_model": "all-MiniLM-L6-v2 (ChromaDB default)",
        }

        if stats["chunk_count"] == 0:
            return stats

        # Get all documents to compute stats
        all_items = self.collection.get(include=["metadatas"])

        if all_items["metadatas"]:
            sources_set: set[str] = set()
            max_mtime = 0
            total_size = 0

            for metadata in all_items["metadatas"]:
                source = metadata.get("source", "")
                if source:
                    sources_set.add(source)
                # Track size
                size = metadata.get("size_bytes", 0)
                if isinstance(size, int | float):
                    total_size += int(size)
                # Track modification time
                mtime = metadata.get("modified_time", 0)
                if isinstance(mtime, int | float) and int(mtime) > max_mtime:
                    max_mtime = int(mtime)

            stats["sources"] = sorted(sources_set)
            stats["total_size_bytes"] = total_size
            if max_mtime > 0:
                from datetime import datetime

                stats["last_modified"] = datetime.fromtimestamp(max_mtime).isoformat()

        return stats

    def _generate_chunk_id(self, chunk: Chunk) -> str:
        """Generate a stable ID for a chunk based on source and index.

        Uses source path and chunk index to create a stable ID that allows
        upsert operations to update existing chunks correctly.

        Args:
            chunk: Chunk to generate ID for

        Returns:
            Stable chunk ID string
        """
        # Use SHA-256 truncated to 16 hex chars (64 bits) to minimize collision risk
        source_hash = hashlib.sha256(str(chunk.source).encode()).hexdigest()[:16]
        return f"{source_hash}_{chunk.chunk_index}"
