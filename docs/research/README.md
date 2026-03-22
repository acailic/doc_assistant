# Research Insights

This directory contains detailed analyses of research papers and their potential applications to the doc_assistant project.

## Papers

### Core Architecture (Foundational)

These papers established the RAG paradigm that doc_assistant follows:

| Paper | Key Insight | doc_assistant Application |
|-------|-------------|---------------------------|
| [RAG (2020)](../research-inspiration.md#1-retrieval-augmented-generation-for-knowledge-intensive-nlp-tasks) | Retrieve before generate | Separate retrieval and generation stages |
| [DPR (2020)](../research-inspiration.md#2-dense-passage-retrieval-for-open-domain-question-answering) | Dense semantic retrieval | Query/chunk embedding similarity |
| [SBERT (2019)](../research-inspiration.md#3-sentence-bert-sentence-embeddings-using-siamese-bert-networks) | Efficient sentence embeddings | Fast semantic similarity search |
| [MiniLM (2020)](../research-inspiration.md#4-minilm-deep-self-attention-distillation-for-task-agnostic-compression-of-pre-trained-transformers) | Compressed embeddings | Local embeddings on developer hardware |
| [Lost in the Middle (2023)](../research-inspiration.md#5-lost-in-the-middle-how-language-models-use-long-contexts) | Context selectivity matters | Bounded retrieval + relevance filtering |

### Emerging Research (2024-2025)

Newer papers with potential future applications:

| Paper | Key Insight | Potential Application |
|-------|-------------|----------------------|
| [RAG Fusion](./rag-fusion.md) | Fusion gains neutralized by re-ranking | Invest in single strong retriever first |
| [AttentionRetriever](./attention-retriever.md) | Attention patterns as retrieval signals | Entity-aware chunking, long-doc handling |
| [INTRA Fact Checking](./fact-checking-intra.md) | Parametric knowledge as fallback | Confidence estimation, doc gap detection |

## Future Reading Queue

Papers identified for future exploration:

- **SciMDR** - Multi-document retrieval for scientific literature
- **Neural Debugger** - Using LLMs to debug retrieval pipelines
- **CXReasonAgent** - Reasoning agents for complex queries
- **Document Navigation** - Long-document navigation strategies
- **Compact World Models** - Efficient knowledge compression
- **MSSR Memory** - Memory systems for sustained retrieval

## How to Add New Papers

1. Read the paper and extract key insights
2. Create a new file: `paper-short-name.md`
3. Include sections:
   - Overview
   - Key Findings
   - Implications for doc_assistant
   - Code Experiments (if applicable)
   - Questions for Investigation
4. Update this README index
5. Update `../research-inspiration.md` main list
