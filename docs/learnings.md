# Learnings

## Scope

This document consolidates the main learnings from building and packaging `doc_assistant` as a standalone repository.

It includes:
- product learnings
- implementation learnings
- retrieval and prompting learnings
- packaging and standalone-repo learnings
- testing and maintenance learnings

It is the canonical place for lessons learned. Other docs may reference specific parts of it, but this file is where they are collected in one place.

## Product Learnings

### 1. The right first product is a CLI, not a platform

The smallest useful version is a command-line tool that developers can run where they already work.

Why this mattered:
- it kept scope narrow
- it made the retrieval pipeline the main thing to prove
- it removed the need to build a UI before validating usefulness

Practical result:
- the project exposes `index`, `query`, `chat`, and `stats` rather than a larger application surface

### 2. "Documentation" is broader than markdown

Real developer knowledge is spread across:
- markdown
- text files
- PDFs
- code files
- JSON and YAML configs

Why this mattered:
- many implementation answers live in code and config, not prose docs
- a markdown-only assistant would miss a large part of the actual knowledge base

Practical result:
- the loader supports multiple file types rather than treating docs as only prose

### 3. Incremental indexing is part of usability, not an optimization detail

If developers have to rebuild the whole index after every small change, the tool becomes annoying quickly.

Why this mattered:
- docs change often
- full rebuilds are acceptable for demos but not for daily workflows

Practical result:
- the loader computes `content_hash`
- the index stores source-to-hash information
- the CLI updates new, changed, unchanged, and deleted files separately

## Ingestion Learnings

### 4. Good metadata is necessary early

The loader does more than return file text. It also attaches:
- file format
- modification time
- size
- content hash

Why this mattered:
- change detection depends on metadata
- downstream features become easier when metadata is preserved consistently

Practical result:
- both indexing and retrieval have enough context to stay auditable and extendable

### 5. PDF support is useful but fragile

PDF ingestion increases coverage, but PDF extraction quality always depends on the source file.

Why this mattered:
- internal docs often include exported design docs, vendor docs, or one-off reference PDFs
- extraction failures should not break the whole indexing run

Practical result:
- PDF loading is isolated and handled with graceful fallback logging instead of crashing the pipeline

## Chunking Learnings

### 6. Structure-aware chunking is worth the extra complexity

A flat fixed-window splitter is simple, but it can separate headings from the content they describe.

Why this mattered:
- internal documentation is usually hierarchical
- users ask section-shaped questions, not just bag-of-words questions

Practical result:
- markdown is split by headers first
- oversized sections are then split recursively
- section metadata can be preserved in chunks

### 7. Chunk quality matters more than theoretical neatness

Exact chunk boundaries are less important than preserving meaning.

Why this mattered:
- perfectly uniform chunks can still be semantically bad
- a slightly uneven but coherent chunk often retrieves better than a mechanically clean one

Practical result:
- the system uses a pragmatic combination of markdown-aware and character-based splitting

### 8. Character-based chunking is a reasonable first tradeoff, but not the end state

Character counts are easy to reason about and configure, but they are only an approximation of model context usage.

Why this mattered:
- the first implementation needed predictable behavior with minimal complexity

Practical result:
- the current chunker uses character size and overlap
- token-aware chunking remains a clear improvement area

## Retrieval Learnings

### 9. Dense retrieval is a strong baseline for developer docs

Semantic vector retrieval is valuable because users often ask questions differently than the docs are written.

Why this mattered:
- developer questions are paraphrased naturally
- exact keyword overlap is often weak even when the right answer exists

Practical result:
- the system uses dense similarity search through ChromaDB

### 10. Dense retrieval alone is not the whole answer

Dense search is effective, but it still has limitations:
- weak lexical matches can be missed
- near-topic chunks can outrank exact but rare terms

Why this mattered:
- some questions depend on exact identifiers, config keys, or filenames

Practical result:
- hybrid retrieval and reranking remain important future improvements

### 11. Retrieval scores are useful as guardrails even if they are not perfect confidence metrics

Similarity scores are not the same as answer correctness, but they are still useful operational signals.

Why this mattered:
- the assistant should avoid confident answers from weak context

Practical result:
- the retriever adds a score
- the answerer uses score thresholds before generating

## Answering Learnings

### 12. The assistant must be allowed to say "I don't know"

Weak retrieval should produce a constrained failure message, not a polished hallucination.

Why this mattered:
- trust collapses quickly if the tool invents answers from unrelated context

Practical result:
- the answerer returns early for low average relevance
- weak chunks are filtered out before prompt construction

### 13. Grounding is more important than eloquence

For this product, a shorter grounded answer is better than a broader speculative one.

Why this mattered:
- the tool is for internal knowledge access, not open-ended brainstorming

Practical result:
- the prompt explicitly tells the model to answer only from provided context
- sources are returned with the answer

### 14. Source visibility increases trust

Users need to know where an answer came from.

Why this mattered:
- internal documentation changes
- users often want to inspect the source directly

Practical result:
- answers include source filenames
- the pipeline tracks sources all the way to the CLI output

### 15. Smaller high-signal context beats dumping everything

More retrieved text is not automatically better.

Why this mattered:
- irrelevant chunks dilute the useful evidence
- long prompts can still reduce answer quality

Practical result:
- retrieval is bounded by `top_k`
- weak chunks are removed before prompt assembly

## CLI and Workflow Learnings

### 16. The interface should map directly to user tasks

Developers do not want to learn a large tool for a simple workflow.

Why this mattered:
- the common tasks are obvious:
  - build the index
  - ask one question
  - ask several questions
  - inspect status

Practical result:
- the CLI commands stay tightly aligned with those four tasks

### 17. Fast failure messages are part of the product

The assistant should explain operational problems clearly.

Why this mattered:
- missing index
- missing API key
- weak retrieval

These are normal states, not exceptional edge cases.

Practical result:
- the CLI and answerer return explicit messages rather than generic tracebacks for expected failures

## Standalone Repository Learnings

### 18. Standalone packaging requires a real package layout

For the repository to install cleanly as its own package, it must expose an importable package directory.

Why this mattered:
- docs alone are not enough to make a project standalone
- the build backend needs a clear package to ship

Practical result:
- the code lives under `doc_assistant/`
- the project script points to `doc_assistant.cli:cli`

### 19. Documentation and invocation paths must match the actual package shape

If docs say one command and packaging exposes another, users lose time immediately.

Why this mattered:
- the project moved from a nested workspace context to standalone-repo usage

Practical result:
- docs now use standalone naming:
  - `doc_assistant`
  - `doc-assistant`
  - `python -m doc_assistant`

### 20. Tests should import the installed package path, not rely on old relative layout assumptions

Relative imports often hide packaging mistakes because they work only in a specific repo layout.

Why this mattered:
- standalone packaging needs test coverage that matches real usage

Practical result:
- tests import `doc_assistant.*` directly

### 21. Dependency declarations must match runtime imports exactly

Packaging problems often come from seemingly small import mismatches.

Why this mattered:
- the chunker imports text splitters from `langchain_text_splitters`
- that means the dependency must be `langchain-text-splitters`, not a vague parent package assumption

Practical result:
- runtime dependencies now reflect the actual imports used by the code

### 22. Supported Python versions should reflect real dependency behavior, not wishful compatibility

A project should not claim support for versions where the dependency stack is noisy or unstable.

Why this mattered:
- the current stack emits warnings on Python 3.14+

Practical result:
- the repo currently declares support for Python `3.11` to `3.13`

## Testing Learnings

### 23. Most of the system should be testable without external APIs

If the whole test suite depends on live API calls, iteration slows down and reliability drops.

Why this mattered:
- loading, chunking, indexing, and retrieval are local behaviors
- those should be validated locally and deterministically

Practical result:
- most tests run without Anthropic access
- live-generation tests are conditional

### 24. Integration tests still matter even in a small repo

Unit tests are not enough for a pipeline-shaped system.

Why this mattered:
- this project only works if the stages fit together:
  - loader
  - chunker
  - indexer
  - retriever
  - answerer

Practical result:
- the repo keeps an end-to-end test for the full flow

### 25. Verification should include installed-entrypoint checks, not just imports

A package can look correct in source form and still fail once installed.

Why this mattered:
- standalone success depends on both:
  - `uv run doc-assistant --help`
  - `uv run python -m doc_assistant --help`

Practical result:
- standalone smoke tests are part of the current operational knowledge for this repo

## Maintenance Learnings

### 26. A small module graph is easier to evolve

The project benefits from clear responsibilities:
- loader
- chunker
- indexer
- retriever
- answerer
- CLI

Why this mattered:
- each stage is understandable in isolation
- behavior changes are easier to localize

Practical result:
- the codebase is still compact enough for fast iteration

### 27. Preserve the distinction between product decisions and research inspiration

Not every good engineering choice comes from a paper.

Why this mattered:
- some decisions are practical product choices:
  - incremental indexing
  - CLI-first UX
  - filename citations
  - standalone packaging

Practical result:
- the research doc focuses on conceptual lineage
- implementation-specific lessons are documented separately here

## Current Open Learnings

These are not completed lessons yet, but they are areas where the project is already pointing to the next round of work:

- hybrid retrieval is likely needed for identifier-heavy queries
- reranking would probably improve prompt quality before answer generation
- token-aware chunking would be more faithful than character-based limits
- richer citations such as section path or excerpts would improve answer auditability
- answer confidence should eventually be evaluated against real task performance, not just similarity scores

## Summary

The biggest lesson is that a useful documentation assistant is not just "LLM plus embeddings." It depends on a chain of practical decisions:
- index the kinds of files teams really use
- preserve document structure where possible
- keep indexing incremental
- refuse weakly grounded answers
- make the CLI easy to use
- package the repo so it actually works standalone

Those details are what turn a demo into a tool.
