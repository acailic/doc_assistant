"""Pydantic models for the documentation assistant."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel


class Document(BaseModel):
    """A loaded document with content and metadata."""

    source: Path
    content: str
    metadata: dict[str, Any] = {}


class Chunk(BaseModel):
    """A chunk of document content for embedding."""

    content: str
    source: Path
    chunk_index: int
    metadata: dict[str, Any] = {}


class Answer(BaseModel):
    """An answer generated from retrieved context."""

    content: str
    sources: list[Path]
    confidence: float = 1.0
