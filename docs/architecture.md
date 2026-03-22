# Architecture

## Overview

The project is a small retrieval-augmented generation CLI for internal documentation. It indexes local files into a persistent vector store, retrieves semantically similar chunks for a user question, and asks Claude to answer strictly from the retrieved context.

High-level flow:

```text
documents -> loader -> chunker -> indexer -> retriever -> answerer -> CLI output
```

## Core Modules

### `loader`

Responsibility:
- Discover supported files recursively
- Load text or PDF content
- Attach file metadata
- Compute a deterministic `content_hash` for change detection

Important implementation detail:
- Incremental indexing depends on `content_hash`, so the loader is not just ingestion. It is also the source of truth for whether a file changed.

### `chunker`

Responsibility:
- Split documents into embedding-friendly chunks
- Preserve markdown structure when possible
- Carry metadata forward into each chunk

Important implementation detail:
- Markdown uses `MarkdownHeaderTextSplitter` first, then falls back to recursive character splitting for large sections or headerless files.
- This is a practical compromise between semantic structure and simple chunk size control.

### `indexer`

Responsibility:
- Store chunks in ChromaDB
- Persist the collection on disk
- Add, upsert, count, clear, and delete source-backed chunks
- Expose indexed source hashes for incremental updates

Important implementation detail:
- Chunk IDs are stable because they are derived from source path plus chunk index.
- Stable IDs make `upsert` work cleanly for changed documents.

### `retriever`

Responsibility:
- Query ChromaDB with the user question
- Convert result rows back into project `Chunk` objects
- Attach retrieval score metadata

Important implementation detail:
- The retriever turns vector distance into a similarity-style score with `1 - distance`.
- That score is later used to decide whether the answerer should trust the retrieved context at all.

### `answerer`

Responsibility:
- Filter low-quality retrieval results
- Build a grounded prompt from retrieved chunks
- Ask Claude for a final answer with source references
- Return confidence and source paths

Important implementation detail:
- The answerer has two guardrails:
  - average relevance threshold before generation
  - per-chunk score threshold before adding text to the prompt
- These checks reduce low-signal prompts and lower the chance of confident but weakly grounded answers.

### `cli`

Responsibility:
- Expose four user workflows:
  - `index`
  - `query`
  - `chat`
  - `stats`

Important implementation detail:
- `index` supports both full rebuilds and incremental updates.
- Incremental mode handles new, changed, unchanged, and deleted files.

## Data Model

### `Document`

Represents a loaded source file:
- `source`
- `content`
- `metadata`

### `Chunk`

Represents a retrievable unit:
- `content`
- `source`
- `chunk_index`
- `metadata`

### `Answer`

Represents the final response:
- `content`
- `sources`
- `confidence`

## Indexing Lifecycle

### Full indexing

Used when:
- the collection does not exist yet
- the user passes `--force`

Process:
1. Load all supported documents
2. Chunk each document
3. Add all chunks to ChromaDB

### Incremental indexing

Used by default after the first run.

Process:
1. Load all current documents
2. Compare each file's `content_hash` with the stored hash
3. Add new files
4. Upsert changed files
5. Remove deleted files from the collection

This is one of the most important product decisions in the project because it keeps indexing cheap enough for normal developer workflows.

## Retrieval and Answering Lifecycle

1. User asks a question.
2. The retriever asks ChromaDB for the top `k` semantically similar chunks.
3. The answerer computes average relevance.
4. If relevance is too low, the pipeline stops early with a grounded failure message.
5. Otherwise, only sufficiently strong chunks are included in the final context.
6. Claude generates an answer constrained by those chunks.
7. The CLI prints the answer, confidence, and source files.

## Why This Shape Works

- Local embeddings and local persistence keep indexing simple to operate.
- Structure-aware markdown chunking improves retrieval quality for real documentation.
- Incremental indexing avoids rebuilding everything after small doc edits.
- Relevance thresholds make the assistant more conservative when retrieval is weak.
- File-level citations keep answers auditable.

## Current Constraints

- Retrieval is pure dense vector retrieval; there is no keyword fallback or reranker.
- The answer generator depends on Anthropic API availability.
- Confidence is retrieval-derived, not calibrated against answer correctness.
- Chunking is character-based after structure splitting, not token-based.
- There is no conversational memory beyond the current chat loop question.

## Natural Next Steps

- Add hybrid retrieval with lexical fallback
- Add reranking before prompt assembly
- Make chunking token-aware
- Cache answer generation for repeated queries
- Add richer source citations such as section path and chunk excerpt
