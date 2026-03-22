# AttentionRetriever: Long Document Retrieval via Attention

**Paper:** AttentionRetriever: Attention Layers are Secretly Long Document Retrievers
**arXiv:** https://arxiv.org/abs/2602.12278
**Year:** 2025

## Overview

This paper introduces a novel approach to long document retrieval using the attention mechanisms of transformer models directly. Instead of treating documents as bags of chunks, it exploits the implicit retrieval signals present in attention patterns.

## Key Innovations

### 1. Attention as Retrieval Signal

Transformer attention layers naturally learn which parts of a document are relevant to which queries. The paper shows these attention patterns can be extracted and used for passage ranking.

### 2. Entity-Based Retrieval

The approach incorporates entity recognition to create context-aware embeddings:
- Named entities (functions, classes, variables in code docs)
- Technical terms
- Cross-references

### 3. Long Document Handling

Unlike chunk-based retrieval which may lose cross-chunk context, attention-based retrieval maintains awareness of document-wide relationships.

## Implications for doc_assistant

### Current Limitation: Chunk Context Loss

The current chunking approach has a known limitation:

```python
# Current: chunks lose cross-section context
def chunk_document(doc):
    # Header-aware splitting preserves some structure
    # but cross-chunk references are lost
    return markdown_splitter.split(doc)
```

A chunk about "configuration" may reference "see the API section above" but that reference is lost when the chunk is retrieved in isolation.

### Potential Enhancement: Entity-Aware Chunking

```python
# Future: enrich chunks with entity context
def chunk_with_entities(doc):
    chunks = markdown_splitter.split(doc)
    entities = extract_entities(doc)  # functions, classes, configs

    for chunk in chunks:
        # Attach entities mentioned in chunk
        chunk.entities = find_entities(chunk.content, entities)
        # Attach cross-references found in chunk
        chunk.references = extract_references(chunk.content)

    return chunks
```

### Potential Enhancement: Attention-Guided Retrieval

```python
# Future: use attention patterns for retrieval scoring
def retrieve_with_attention(query, chunks):
    # Standard semantic retrieval
    candidates = dense_retriever(query, chunks, k=20)

    # Re-score using attention patterns
    for chunk in candidates:
        attention_score = compute_attention_relevance(query, chunk)
        chunk.final_score = 0.7 * chunk.semantic_score + 0.3 * attention_score

    return sorted(candidates, key=lambda c: c.final_score, reverse=True)
```

## Practical Considerations

### Complexity Trade-off

Attention-based retrieval adds significant complexity:
- Requires access to model internals
- More computationally expensive than simple similarity
- May not justify itself for small-to-medium documentation sets

### When to Consider This Approach

1. **Large documentation corpora** (10,000+ documents)
2. **Highly cross-referenced docs** (lots of internal links)
3. **Long technical documents** (API references, architecture docs)
4. **User queries requiring context synthesis**

### Current Recommendation

For doc_assistant's target use case (internal team documentation, typically <1,000 documents):

> Stick with dense retrieval + relevance filtering. Attention-based retrieval is an advanced optimization for scale.

## Code Experiments

### Simple Entity Extraction (Low-Cost Enhancement)

```python
import re

def extract_code_entities(text):
    """Extract potential code entities from documentation."""
    # Function/method names
    functions = re.findall(r'\b([a-z_][a-z0-9_]*)\s*\(', text)
    # Class names (CamelCase)
    classes = re.findall(r'\b([A-Z][a-zA-Z0-9]*)\b', text)
    # Config keys
    configs = re.findall(r'`([^`]+)`', text)

    return {
        'functions': set(functions),
        'classes': set(classes),
        'configs': set(configs)
    }

def attach_entities_to_chunks(chunks):
    """Enrich chunks with extracted entities."""
    for chunk in chunks:
        chunk.metadata['entities'] = extract_code_entities(chunk.content)
    return chunks
```

This lightweight entity extraction could improve retrieval for code documentation without requiring attention mechanism access.

## Questions for Further Investigation

1. What entity types are most predictive of relevant retrieval for technical docs?
2. Would cross-reference tracking between chunks improve answer quality?
3. At what document length does attention-based retrieval become worthwhile?
