# Implementation Process

## Goal

Build a developer-facing assistant that can answer questions from local project documentation without requiring a custom search UI or manual wiki hunting.

The implementation follows a pragmatic RAG shape:
- local document ingestion
- semantic chunk retrieval
- LLM answer synthesis from retrieved context

## Build Sequence

### 1. Define the smallest useful product

The first useful version is not a full knowledge platform. It is a CLI that can:
- index a docs directory
- answer one question
- run an interactive chat loop

This scope is important. It keeps the surface area small while proving the core retrieval pipeline.

### 2. Standardize document ingestion

The loader supports the file types developers actually keep knowledge in:
- markdown
- text
- PDF
- source files
- JSON/YAML config files

Key learning:
- "documentation" in real teams is distributed across prose, code, and config. Restricting ingestion to markdown alone would make the assistant much less useful.

### 3. Preserve document structure during chunking

A naive fixed-window chunker is easy to build but often breaks headings away from the content they describe.

The current implementation therefore:
- uses markdown header-aware splitting first
- falls back to recursive character splitting
- keeps overlap for continuity

Key learning:
- structure matters more than chunk size purity for docs-heavy retrieval.

### 4. Choose a low-friction vector store

ChromaDB was selected because it provides:
- persistent local storage
- built-in collection management
- local embedding support
- a simple API for small tools

Key learning:
- for a local CLI, operational simplicity matters more than theoretical flexibility.

### 5. Make indexing incremental

Full rebuilds are acceptable for demos but annoying in daily usage.

The project therefore adds:
- content hashing in the loader
- source-to-hash tracking in the index
- add/update/remove behavior in the CLI indexing command

Key learning:
- incremental indexing is not a nice-to-have. It is part of the product experience.

### 6. Add conservative answer generation

The assistant should not generate polished nonsense from weak retrieval.

The answer generator therefore:
- computes average retrieval relevance
- refuses to answer when relevance is too low
- filters weak chunks before prompt assembly
- instructs the model to answer only from provided context

Key learning:
- retrieval quality control is as important as model quality.

### 7. Wrap it in a simple CLI

The CLI keeps the workflow close to where developers already work.

Commands were kept minimal:
- `index`
- `query`
- `chat`
- `stats`

Key learning:
- if the workflow is not one command away, developers stop using it.

## Practical Learnings

### Learning 1: local-first is the right default for indexing

Using local embeddings and local persistence reduces secrets management, cost, and deployment friction. Only final answer generation requires an external API.

### Learning 2: markdown deserves special handling

A lot of internal documentation is hierarchical. Preserving section boundaries helps retrieval stay aligned with how humans browse docs.

### Learning 3: "confidence" should start from retrieval, not generation style

The current confidence value is derived from similarity scores. That is imperfect, but it is still better than trusting how confident the model sounds.

### Learning 4: deleted files matter

Index freshness is not just about additions and updates. If old content is not removed, stale answers become a real risk.

### Learning 5: tests should isolate external dependency costs

The test suite keeps most behavior local and only exercises live answer generation when an API key is available. That preserves fast feedback for core logic.

## Implementation Choices That Paid Off

- Stable chunk IDs made upserts simple.
- Metadata propagation made future features easier.
- Threshold-based early returns kept bad queries from becoming expensive API calls.
- A small number of well-scoped modules made the pipeline easy to reason about.

## Tradeoffs We Accepted

- Dense retrieval only, without lexical fallback
- Character-based chunk sizing instead of token-based chunk sizing
- Single-turn grounded generation instead of richer conversation memory
- Basic confidence estimation instead of calibrated evaluation metrics

These are reasonable tradeoffs for a first robust implementation.

## What To Improve Next

1. Add hybrid retrieval and reranking.
2. Store richer metadata such as section path for all result displays.
3. Evaluate chunk size and overlap empirically on a real internal docs corpus.
4. Add regression fixtures for stale-doc, deleted-doc, and multi-file citation cases.
5. Consider answer streaming in chat mode.
