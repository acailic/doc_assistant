"""Text chunking for embedding."""

from collections.abc import Sequence

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from ..models import Chunk, Document


class TextChunker:
    """Split documents into chunks for embedding.

    For markdown files, uses structure-aware splitting that preserves
    header hierarchy. For other formats, uses recursive character splitting.
    """

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """Initialize chunker.

        Args:
            chunk_size: Target size of each chunk in characters
            overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        # Markdown splitter preserves header structure
        self.md_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
            ],
            strip_headers=False,
        )

    def chunk(self, document: Document) -> list[Chunk]:
        """Split a document into chunks.

        For markdown files, uses structure-aware splitting to preserve
        header hierarchy. For other formats, uses recursive character splitting.

        Args:
            document: Document to chunk

        Returns:
            List of Chunk objects
        """
        if document.source.suffix.lower() == ".md":
            return self._chunk_markdown(document)
        return self._chunk_text(document)

    def _chunk_text(self, document: Document) -> list[Chunk]:
        """Split a document using recursive character splitting.

        Args:
            document: Document to chunk

        Returns:
            List of Chunk objects
        """
        texts = self.splitter.split_text(document.content)

        return [
            Chunk(
                content=text,
                source=document.source,
                chunk_index=i,
                metadata={**document.metadata, "chunk_index": i},
            )
            for i, text in enumerate(texts)
        ]

    def _chunk_markdown(self, document: Document) -> list[Chunk]:
        """Split a markdown document preserving header structure.

        Args:
            document: Document to chunk

        Returns:
            List of Chunk objects with header metadata
        """
        # Try markdown-aware splitting first
        md_chunks = self.md_splitter.split_text(document.content)

        # If no headers found, fall back to text splitting
        if not md_chunks:
            return self._chunk_text(document)

        chunks = []
        chunk_index = 0

        for md_chunk in md_chunks:
            content = md_chunk.page_content
            header_metadata = md_chunk.metadata or {}

            # Build section path from headers
            section_parts = []
            for level in ["h1", "h2", "h3"]:
                if header_metadata.get(level):
                    section_parts.append(header_metadata[level])
            section_path = " > ".join(section_parts) if section_parts else None

            # If chunk is too large, further split it
            if len(content) > self.chunk_size:
                sub_texts = self.splitter.split_text(content)
                for sub_text in sub_texts:
                    chunk_metadata = {
                        **document.metadata,
                        "chunk_index": chunk_index,
                        **header_metadata,
                    }
                    if section_path:
                        chunk_metadata["section_path"] = section_path

                    chunks.append(
                        Chunk(
                            content=sub_text,
                            source=document.source,
                            chunk_index=chunk_index,
                            metadata=chunk_metadata,
                        )
                    )
                    chunk_index += 1
            else:
                chunk_metadata = {
                    **document.metadata,
                    "chunk_index": chunk_index,
                    **header_metadata,
                }
                if section_path:
                    chunk_metadata["section_path"] = section_path

                chunks.append(
                    Chunk(
                        content=content,
                        source=document.source,
                        chunk_index=chunk_index,
                        metadata=chunk_metadata,
                    )
                )
                chunk_index += 1

        return chunks

    def chunk_all(self, documents: Sequence[Document]) -> list[Chunk]:
        """Chunk multiple documents.

        Args:
            documents: Sequence of documents to chunk

        Returns:
            List of all chunks from all documents
        """
        all_chunks = []
        for doc in documents:
            all_chunks.extend(self.chunk(doc))
        return all_chunks
