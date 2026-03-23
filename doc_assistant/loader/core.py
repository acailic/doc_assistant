"""Document loading and parsing."""

import hashlib
import logging
import os
from collections.abc import Iterator
from pathlib import Path

from ..models import Document

logger = logging.getLogger(__name__)

# Supported file formats and their loaders
SUPPORTED_FORMATS = {
    ".md": "markdown",
    ".txt": "text",
    ".pdf": "pdf",
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
}


class DocumentLoader:
    """Load and parse documents from a directory."""

    def __init__(self, docs_dir: Path):
        """Initialize loader with documents directory.

        Args:
            docs_dir: Path to directory containing documents

        Raises:
            FileNotFoundError: If docs_dir doesn't exist
        """
        self.docs_dir = Path(docs_dir)
        if not self.docs_dir.exists():
            raise FileNotFoundError(f"Directory not found: {self.docs_dir}")

    def load(self) -> Iterator[Document]:
        """Load all supported documents from the directory.

        Yields:
            Document objects with content and metadata (including content_hash)
        """
        for file_path in self._discover_files():
            content = self._load_file(file_path)
            if content:
                metadata = self._extract_metadata(file_path)
                # Add content hash for change detection
                metadata["content_hash"] = hashlib.sha256(content.encode()).hexdigest()
                yield Document(
                    source=file_path,
                    content=content,
                    metadata=metadata,
                )

    def _discover_files(self) -> Iterator[Path]:
        """Recursively discover supported files."""
        for root, _dirs, files in os.walk(self.docs_dir):
            for filename in files:
                file_path = Path(root) / filename
                if file_path.suffix.lower() in SUPPORTED_FORMATS:
                    yield file_path

    def _load_file(self, file_path: Path) -> str | None:
        """Load content from a file based on its format."""
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return self._load_pdf(file_path)
        # Text-based formats (md, txt, py, js, ts, json, yaml)
        return self._load_text(file_path)

    def _load_text(self, file_path: Path) -> str | None:
        """Load text content from a file."""
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to load text file {file_path}: {e}")
            return None

    def _load_pdf(self, file_path: Path) -> str | None:
        """Load text content from a PDF file."""
        try:
            import fitz  # PyMuPDF

            text_parts = []
            with fitz.open(file_path) as doc:
                for page in doc:
                    text_parts.append(page.get_text())
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.warning(f"Failed to load PDF file {file_path}: {e}")
            return None

    def _extract_metadata(self, file_path: Path) -> dict:
        """Extract metadata from a file."""
        suffix = file_path.suffix.lower()
        stat = file_path.stat()

        return {
            "format": SUPPORTED_FORMATS.get(suffix, "unknown"),
            "modified_time": int(stat.st_mtime),
            "size_bytes": stat.st_size,
        }
