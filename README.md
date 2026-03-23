# Internal Developer Docs Assistant

**Query your documentation in natural language.**

A RAG-powered CLI tool that indexes your internal documentation (markdown, PDF, code, configs) and lets you ask questions in plain English.

## The Problem

- Searching through wikis, READMEs, and code comments is time-consuming
- You know what you want but not where to find it
- Context switching between docs and work disrupts flow

## The Solution

Just ask: "How do I configure authentication?" or "What's the API rate limit?"

## Installation

```bash
# Clone the repository
git clone https://github.com/acailic/doc_assistant.git
cd doc_assistant

# Install dependencies
uv sync
```

**Prerequisites:**
- Python 3.11 to 3.13
- `ANTHROPIC_API_KEY` environment variable set
- Embeddings run locally via ChromaDB (no API key needed)

## Quick Start

### 1. Index Your Documentation

```bash
uv run doc-assistant index --docs ./my_docs/
```

This scans all supported files (md, txt, pdf, py, js, ts, json, yaml) and creates a vector index.

### 2. Query Your Docs

```bash
uv run doc-assistant query --docs ./my_docs/ "How do I configure the database connection?"
```

### 3. Interactive Chat

```bash
uv run doc-assistant chat --docs ./my_docs/
```

Start an interactive session for multiple questions.

## Usage Examples

### Index a Project's Docs

```bash
# Index your project's documentation
uv run doc-assistant index --docs ./docs/

# Or a specific project
uv run doc-assistant index --docs ~/projects/my-api/docs/
```

### Query Examples

```bash
# Configuration questions
uv run doc-assistant query --docs . "What environment variables do I need?"

# Architecture questions
uv run doc-assistant query --docs . "How does the authentication flow work?"

# Troubleshooting
uv run doc-assistant query --docs . "How do I fix the CORS error?"
```

### Interactive Session

```bash
$ uv run doc-assistant chat --docs .

💬 Interactive chat (type 'exit' to quit)

You: What's the default chunk size?
💡 The default chunk size is 1000 characters with 200 character overlap...

You: Can I change it?
💡 Yes, use the --chunk-size and --overlap flags when indexing...

You: exit
Goodbye!
```

## Supported Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| Markdown | .md | Full support |
| Text | .txt | Full support |
| PDF | .pdf | Text extraction via PyMuPDF |
| Python | .py | Code and comments |
| JavaScript | .js | Code and comments |
| TypeScript | .ts | Code and comments |
| JSON | .json | Config files |
| YAML | .yaml, .yml | Config files |

## Commands

### `index`

Index documents for querying.

```bash
uv run doc-assistant index --docs ./my_docs/ [OPTIONS]

Options:
  --docs PATH          Directory containing documentation (required)
  --persist-dir PATH   Where to store the index (default: .data/doc_assistant/)
  --chunk-size N       Chunk size in characters (default: 1000)
  --overlap N          Chunk overlap (default: 200)
  --verbose            Show detailed progress
```

### `query`

Ask a one-shot question.

```bash
uv run doc-assistant query --docs ./my_docs/ "your question"

Options:
  --top-k N           Number of chunks to retrieve (default: 5)
```

### `chat`

Start interactive session.

```bash
uv run doc-assistant chat --docs ./my_docs/
```

### `stats`

Show index statistics.

```bash
uv run doc-assistant stats
```

## How It Works

1. **Indexing**: Documents are loaded, split into chunks (structure-aware for markdown), and embedded using ChromaDB's local embeddings (all-MiniLM-L6-v2)
2. **Storage**: Chunks and embeddings stored in ChromaDB (persistent vector database)
3. **Querying**: Your question is embedded locally, similar chunks are found via cosine similarity
4. **Answering**: Claude generates an answer from the relevant chunks with citations

```
docs/ → Loader → Chunker → ChromaDB → Retriever → Claude → Answer
```

## Configuration

### Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | Yes | Claude API for answers |

**Note:** Embeddings run locally via ChromaDB's default model (all-MiniLM-L6-v2). No API key or external service needed.

### Index Storage

The index is stored in `.data/doc_assistant/` by default. This persists between sessions, so you only need to re-index when your docs change.

## Troubleshooting

### "No index found"

Run the `index` command first:
```bash
uv run doc-assistant index --docs ./my_docs/
```

### "API key not found"

Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY=your-key
```

### "No relevant documentation found"

Try:
1. Re-index with more documents
2. Rephrase your question
3. Increase `--top-k` to retrieve more context

## Project Docs

Additional project documentation lives in [`docs/`](./docs/README.md):

- [`docs/README.md`](./docs/README.md) - Documentation index
- [`docs/architecture.md`](./docs/architecture.md) - System architecture
- [`docs/implementation-process.md`](./docs/implementation-process.md) - How this was built
- [`docs/learnings.md`](./docs/learnings.md) - Consolidated lessons learned
- [`docs/research-inspiration.md`](./docs/research-inspiration.md) - Research and inspiration sources

## License

MIT
