# Research Inspiration

## Scope Note

This document maps research papers to the design that is implemented in this repository today. It is not presented as a verified historical reading log. It is the paper set that best explains the current system choices.

## Core Papers

### 1. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks

- Authors: Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Kuttler, Mike Lewis, Wen-tau Yih, Tim Rocktaschel, Sebastian Riedel, Douwe Kiela
- Year: 2020
- Source: https://arxiv.org/abs/2005.11401

Why it matters here:
- This paper is the clearest conceptual ancestor of the project.
- The project follows the same broad pattern: retrieve external context first, then generate the answer from that context.

Concrete influence on this codebase:
- separate retrieval and generation stages
- grounding the answer in retrieved passages instead of relying only on model memory
- returning source-backed answers rather than free-form completions

Main insight:
- generation quality improves when factual context is retrieved at query time rather than baked only into parametric weights

### 2. Dense Passage Retrieval for Open-Domain Question Answering

- Authors: Vladimir Karpukhin, Barlas Oguz, Sewon Min, Patrick Lewis, Ledell Wu, Sergey Edunov, Danqi Chen, Wen-tau Yih
- Year: 2020
- Source: https://aclanthology.org/2020.emnlp-main.550/

Why it matters here:
- The retriever in this project is a dense semantic retriever over chunk embeddings.
- That design is much closer to DPR than to classic keyword-only search.

Concrete influence on this codebase:
- embed the query and chunks into the same vector space
- retrieve by semantic similarity
- treat passage selection as a first-class step before answer generation

Main insight:
- dense representations can retrieve relevant passages even when user wording does not match document wording exactly

### 3. Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks

- Authors: Nils Reimers, Iryna Gurevych
- Year: 2019
- Source: https://arxiv.org/abs/1908.10084

Why it matters here:
- The local embedding strategy used by Chroma's default stack sits in the practical sentence-embedding tradition that SBERT helped establish.
- This project depends on fast semantic similarity over many chunks, which is exactly the use case SBERT unlocked in practice.

Concrete influence on this codebase:
- chunk-level semantic embeddings
- cosine-style nearest-neighbor retrieval
- prioritizing cheap similarity search over cross-encoding every query/chunk pair

Main insight:
- sentence and passage embeddings make semantic search operationally feasible for real applications

### 4. MiniLM: Deep Self-Attention Distillation for Task-Agnostic Compression of Pre-Trained Transformers

- Authors: Wenhui Wang, Furu Wei, Li Dong, Hangbo Bao, Nan Yang, Ming Zhou
- Year: 2020
- Source: https://arxiv.org/abs/2002.10957

Why it matters here:
- The implementation relies on ChromaDB's local default embedding path, commonly associated with compact MiniLM-based sentence embedding models such as `all-MiniLM-L6-v2`.
- That makes MiniLM relevant as the efficiency backbone behind local semantic indexing.

Concrete influence on this codebase:
- practical local embeddings on developer hardware
- lower-latency indexing and retrieval
- a compact model choice that fits a CLI workflow better than heavier encoders

Main insight:
- compressed transformer representations can preserve enough quality to make local semantic retrieval practical

### 5. Lost in the Middle: How Language Models Use Long Contexts

- Authors: Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, Percy Liang
- Year: 2023
- Source: https://arxiv.org/abs/2307.03172

Why it matters here:
- Even when long context windows are available, blindly stuffing more chunks into the prompt is not automatically better.
- This project already reflects that lesson by keeping retrieval bounded and filtering weak chunks before prompt assembly.

Concrete influence on this codebase:
- `top_k` retrieval instead of dumping the whole corpus
- relevance thresholds before generation
- a bias toward smaller, higher-signal grounded contexts

Main insight:
- context quality and placement matter; more context can still produce worse use of evidence

## Important Engineering Inference

Not every implemented choice maps cleanly to a single paper.

Examples:
- markdown header-aware chunking is mainly an engineering adaptation to documentation structure
- incremental indexing is a product and systems decision, not a direct research-paper feature
- source-path citations are a usability and trust decision more than a modeling result

Those choices are still consistent with the research direction above, but they are best understood as practical implementation refinements rather than direct paper reproductions.

## How The Papers Connect To The Current Pipeline

```text
SBERT / MiniLM -> efficient local semantic embeddings
DPR -> dense passage retrieval over chunk vectors
RAG -> retrieve first, generate second
Lost in the Middle -> keep prompt context selective and high-signal
```

## Summary

The project does not try to reproduce any one paper exactly. Instead, it combines:
- RAG for overall architecture
- DPR-style dense retrieval for passage selection
- SBERT/MiniLM-style efficient embeddings for local search
- long-context caution from recent LLM research to keep prompts selective
