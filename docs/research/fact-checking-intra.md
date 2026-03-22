# INTRA: Fact Checking Without Retrieval

**Paper:** Leveraging LLM Parametric Knowledge for Fact Checking without Retrieval
**arXiv:** https://arxiv.org/abs/2603.05471
**Year:** 2025

## Overview

This paper demonstrates that Large Language Models can perform fact-checking using their internal (parametric) knowledge without external retrieval. The approach, called INTRA, shows that model-internal representations contain enough signal to validate claims.

## Key Findings

### 1. Parametric Knowledge is Real

LLMs trained on large corpora encode factual knowledge in their weights. This knowledge can be accessed and used for verification without retrieving external documents.

### 2. Internal Representations as Confidence Signal

The paper shows that specific internal activations correlate with factual accuracy. This provides a model-native confidence signal.

### 3. Complementary to Retrieval

Parametric verification works best as a complement to, not replacement for, retrieval-based systems:
- Retrieval provides evidence and citations
- Parametric knowledge validates plausibility
- Together they provide robust fact-checking

## Implications for doc_assistant

### Current Architecture: Retrieval-Only Confidence

```python
# Current: confidence derived from retrieval similarity
def compute_confidence(retrieved_chunks):
    if not retrieved_chunks:
        return 0.0

    avg_similarity = sum(c.score for c in retrieved_chunks) / len(retrieved_chunks)

    if avg_similarity < 0.5:
        return 0.0  # Refuse to answer
    elif avg_similarity < 0.7:
        return 0.5  # Low confidence
    else:
        return min(1.0, avg_similarity)  # High confidence
```

This approach has a gap: what if retrieval returns nothing but the model knows the answer from its training?

### Potential Enhancement: Hybrid Confidence

```python
# Future: combine retrieval and parametric confidence
def compute_hybrid_confidence(query, retrieved_chunks, model):
    # Retrieval-based confidence (current approach)
    retrieval_conf = compute_retrieval_confidence(retrieved_chunks)

    if retrieval_conf > 0.7:
        # Strong retrieval evidence - use it
        return retrieval_conf, "retrieval_strong"

    # Weak retrieval - check parametric knowledge
    parametric_conf = model.check_internal_confidence(query)

    if parametric_conf > 0.8 and retrieval_conf < 0.3:
        # Model knows something but docs don't cover it
        return parametric_conf * 0.7, "parametric_fallback"

    if parametric_conf > 0.5 and retrieval_conf > 0.3:
        # Both have some signal - moderate confidence
        return (retrieval_conf + parametric_conf) / 2, "hybrid"

    # Neither has strong signal
    return 0.0, "insufficient"
```

### Practical Use Case: Documentation Gaps

```python
# Scenario: User asks about Python 3.12 feature
# Docs only cover Python 3.10

def handle_potential_doc_gap(query, retrieved_chunks, model):
    if retrieval_is_weak(retrieved_chunks):
        # Check if this is a known gap vs. unknown topic
        if model.knows_topic(query):
            # Model knows about it, but our docs don't cover it
            return Answer(
                content="Our documentation doesn't cover this, but generally...",
                confidence=0.5,
                sources=[],  # No sources - not in our docs
                warning="This answer is based on general knowledge, not your documentation"
            )
        else:
            # Neither docs nor model know
            return Answer(
                content="I don't have enough information to answer.",
                confidence=0.0,
                sources=[],
                warning=None
            )
```

## Practical Considerations

### When Parametric Fallback Helps

1. **Documentation gaps** - When users ask about topics adjacent to documented content
2. **Version differences** - When docs cover older versions but user asks about newer
3. **General concepts** - When questions are conceptual rather than implementation-specific

### When to Avoid Parametric Fallback

1. **Company-specific information** - Policies, procedures, internal APIs
2. **Recently changed content** - Model training cutoff issues
3. **High-stakes answers** - Security, compliance, production configurations

### Implementation Complexity

Parametric confidence requires:
- Access to model internals or confidence APIs
- Calibration for your domain
- Careful prompting to separate "I know this" from "I'm guessing"

### Current Recommendation

For doc_assistant's primary use case (internal documentation QA):

> Keep retrieval-only confidence. The complexity of parametric fallback doesn't justify itself for documentation lookup, where we specifically want answers grounded in the provided docs.

However, implement a **gap detection** signal:

```python
def detect_doc_gap(query, retrieved_chunks, model):
    """Detect when user asks something docs should cover but don't."""
    if retrieval_is_weak(retrieved_chunks):
        # Check if this seems like a question our docs *should* answer
        if looks_like_doc_question(query) and model.knows_topic(query):
            return DocGap(
                topic=extract_topic(query),
                suggestion="Consider adding documentation for this topic"
            )
    return None
```

## Code Experiments

### Simple Gap Detection

```python
def should_be_in_docs(query, retrieved_chunks, llm_client):
    """Check if weak retrieval is likely a documentation gap."""
    if len(retrieved_chunks) > 0 and retrieved_chunks[0].score > 0.3:
        return None  # Found something, probably not a gap

    # Ask model if this seems like a question our docs should cover
    prompt = f"""
    A user asked: "{query}"

    Is this a question that internal developer documentation would typically cover?
    Answer only: YES or NO
    """

    response = llm_client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=10,
        messages=[{"role": "user", "content": prompt}]
    )

    if "YES" in response.content[0].text:
        return {
            "gap_detected": True,
            "query": query,
            "suggestion": f"Consider adding documentation for: {query}"
        }

    return None
```

## Questions for Further Investigation

1. How do we calibrate parametric confidence for technical documentation?
2. What's the right user experience for "I know this but it's not in your docs"?
3. Should gap detection feed back into documentation maintenance workflows?
