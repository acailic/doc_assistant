# Documentation

This folder collects the working documentation for the internal developer docs assistant.

This project should be described here as a standalone repository. Use standalone naming such as `doc_assistant` or the `doc-assistant` CLI, not `ai_working.doc_assistant`.

It is intended to answer four questions:

1. What does the project do?
2. How is it implemented?
3. What did we learn while building it?
4. Which research papers best explain the design choices?

## Document Map

- [Architecture](./architecture.md): system shape, module responsibilities, and request flow
- [Implementation Process](./implementation-process.md): build sequence, tradeoffs, and practical learnings
- [Learnings](./learnings.md): consolidated lessons from building, packaging, testing, and operating the project
- [Research Inspiration](./research-inspiration.md): papers that map most directly to the current RAG design

### Research Deep Dives

Detailed analysis of individual papers and their applications:

- [RAG Fusion](./research/rag-fusion.md): Industry deployment lessons, fusion vs. re-ranking trade-offs
- [AttentionRetriever](./research/attention-retriever.md): Long document retrieval via attention mechanisms
- [Fact Checking (INTRA)](./research/fact-checking-intra.md): Parametric knowledge as fallback validation

## Scope Note

The research paper list is based on the current implementation, not on a historical log of every article ever read during development. In other words, it documents the papers that best explain the design that exists in this repository today.
