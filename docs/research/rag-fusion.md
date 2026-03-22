# RAG Fusion: Industry Deployment Lessons

**Paper:** Scaling Retrieval Augmented Generation with RAG Fusion: Lessons from an Industry Deployment
**arXiv:** https://arxiv.org/abs/2603.02153
**Year:** 2025

## Overview

This paper evaluates Retrieval-Augmented Generation Fusion (RAG Fusion) in a real production environment, providing empirical data on what actually works at scale. It specifically examines the relationship between retrieval fusion and re-ranking.

## Key Findings

### 1. Fusion Increases Raw Recall

RAG Fusion (combining results from multiple retrievers) does increase the raw number of relevant documents retrieved. This is consistent with intuition: more retrieval paths = more coverage.

### 2. Fusion Gains Neutralized by Re-ranking

The critical finding is that when a strong re-ranking step is applied, the benefits of fusion largely disappear. A single strong retriever + good re-ranker often matches or exceeds fusion + re-ranking.

### 3. Fusion Adds Overhead

Fusion introduces:
- Multiple retrieval calls
- Result merging complexity
- Increased latency
- Higher computational cost

## Implications for doc_assistant

### Current Design Choices Validated

The doc_assistant currently uses a single dense retriever (ChromaDB with MiniLM embeddings). This paper suggests that:

1. **Don't rush to add fusion** - A single well-tuned retriever with proper similarity thresholds may be sufficient
2. **Invest in relevance scoring** - The paper's re-ranking insight suggests our relevance threshold approach is aligned with best practices
3. **Keep it simple** - Fusion complexity may not justify itself for documentation QA

### Potential Future Enhancements

If retrieval quality becomes a bottleneck:

1. **Add re-ranking first** - Before fusion, implement a cross-encoder re-ranker to improve precision on retrieved results
2. **Then consider fusion** - Only add multiple retrieval paths if re-ranking alone doesn't meet quality targets
3. **Measure carefully** - Any fusion approach should be A/B tested against single-retriever + re-ranking baseline

### Practical Takeaway

> "Fusion is not a free lunch. If re-ranking is already strong, fusion adds overhead without proportional benefit."

For a CLI tool focused on developer documentation, latency and simplicity matter. This paper supports the current architecture: strong single retriever + relevance filtering.

## Code Implications

### What NOT to Do

```python
# Premature optimization - adding fusion before re-ranking
def retrieve_with_fusion(query):
    results1 = dense_retriever(query)
    results2 = sparse_retriever(query)  # BM25
    results3 = hybrid_retriever(query)
    return merge_and_dedupe(results1, results2, results3)
```

### Better Approach (Current Architecture)

```python
# Strong single retriever + relevance filtering (what we have)
def retrieve_single_strong(query, threshold=0.7):
    results = dense_retriever(query)
    filtered = [r for r in results if r.score > threshold]
    return filtered
```

### Future Enhancement Path

```python
# If needed, add re-ranking first
def retrieve_with_rerank(query, threshold=0.7):
    candidates = dense_retriever(query, k=20)  # Get more candidates
    reranked = cross_encoder_rerank(query, candidates)
    return [r for r in reranked if r.score > threshold][:5]
```

## Questions for Further Investigation

1. What is the optimal relevance threshold for documentation QA?
2. Would a domain-specific re-ranker improve precision for technical docs?
3. At what corpus size does single-retriever performance degrade?
