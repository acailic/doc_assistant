"""CLI interface for documentation assistant."""

import logging
from pathlib import Path

import click

from . import __version__
from .answerer.core import AnswerGenerator
from .chunker.core import TextChunker
from .indexer.core import IndexManager
from .loader.core import DocumentLoader
from .retriever.core import Retriever


@click.group()
@click.version_option(version=__version__, prog_name="doc-assistant")
def cli() -> None:
    """Internal Developer Docs Assistant - Query your documentation in natural language."""
    pass


@cli.command()
@click.option("--docs", "-d", required=True, type=click.Path(exists=True), help="Directory containing documentation")
@click.option("--persist-dir", "-p", default=".data/doc_assistant", help="Directory to store index")
@click.option("--chunk-size", default=1000, type=click.IntRange(min=50), help="Chunk size in characters (min 50)")
@click.option("--overlap", default=200, type=click.IntRange(min=0), help="Chunk overlap in characters (min 0)")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--force", "-f", is_flag=True, help="Force full re-index (ignore existing index)")
def index(docs: str, persist_dir: str, chunk_size: int, overlap: int, verbose: bool, force: bool) -> None:
    """Index documents for querying.

    By default, performs incremental indexing - only re-indexing changed files.
    Use --force to perform a full re-index.
    """
    # IMP-4: Configure logging when verbose mode is enabled
    if verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if overlap >= chunk_size:
        click.echo("❌ Error: overlap must be less than chunk-size", err=True)
        raise SystemExit(1)

    docs_path = Path(docs)
    persist_path = Path(persist_dir)

    click.echo(f"📚 Indexing documents from: {docs_path}")

    # Initialize components
    loader = DocumentLoader(docs_path)
    chunker = TextChunker(chunk_size=chunk_size, overlap=overlap)
    manager = IndexManager(persist_dir=persist_path)

    # Force full re-index
    if force:
        if verbose:
            click.echo("  Force flag set - performing full re-index")
        manager.clear()

    # Load all current documents
    all_docs = list(loader.load())

    if force:
        # Full re-index: add all chunks
        total_chunks = 0
        for doc in all_docs:
            if verbose:
                click.echo(f"  Processing: {doc.source.name}")
            chunks = chunker.chunk(doc)
            manager.add_chunks(chunks)
            total_chunks += len(chunks)

        click.echo(f"\n✅ Indexed {len(all_docs)} documents ({total_chunks} chunks)")
    else:
        # Incremental indexing
        indexed_sources = manager.get_indexed_sources()

        new_count = 0
        updated_count = 0
        unchanged_count = 0
        total_new_chunks = 0
        total_updated_chunks = 0

        # Track which sources we've seen
        current_sources: set[str] = set()

        for doc in all_docs:
            source_str = str(doc.source)
            current_sources.add(source_str)
            content_hash = doc.metadata.get("content_hash", "")
            indexed_hash = indexed_sources.get(source_str)

            if indexed_hash is None:
                # New file
                if verbose:
                    click.echo(f"  New: {doc.source.name}")
                chunks = chunker.chunk(doc)
                manager.add_chunks(chunks)
                new_count += 1
                total_new_chunks += len(chunks)
            elif indexed_hash != content_hash:
                # Changed file - IMP-1: Use remove + add instead of upsert to handle shrinking files
                if verbose:
                    click.echo(f"  Updated: {doc.source.name}")
                manager.remove_source(source_str)
                chunks = chunker.chunk(doc)
                manager.add_chunks(chunks)
                updated_count += 1
                total_updated_chunks += len(chunks)
            else:
                # Unchanged file
                unchanged_count += 1

        # Remove chunks for deleted files
        removed_count = 0
        for source_str in indexed_sources:
            if source_str not in current_sources:
                if verbose:
                    click.echo(f"  Removed: {Path(source_str).name}")
                manager.remove_source(source_str)
                removed_count += 1

        # Report results
        click.echo("\n✅ Index updated:")
        click.echo(f"   {new_count} new ({total_new_chunks} chunks)")
        click.echo(f"   {updated_count} updated ({total_updated_chunks} chunks)")
        click.echo(f"   {unchanged_count} unchanged")
        click.echo(f"   {removed_count} removed")

    click.echo(f"   Index stored in: {persist_path}")


@cli.command()
@click.option("--persist-dir", "-p", default=".data/doc_assistant", help="Directory where index is stored")
@click.option("--top-k", default=5, help="Number of chunks to retrieve")
@click.option("--model", "-m", default="claude-sonnet-4-20250514", help="Claude model to use")
@click.argument("question")
def query(persist_dir: str, top_k: int, model: str, question: str) -> None:
    """Query the documentation with a question."""
    persist_path = Path(persist_dir)

    if not persist_path.exists():
        click.echo("❌ No index found. Run 'index' command first.", err=True)
        raise SystemExit(1)

    # Initialize components
    manager = IndexManager(persist_dir=persist_path)
    retriever = Retriever(index_manager=manager)
    generator = AnswerGenerator(model=model)

    click.echo(f"\n❓ Question: {question}\n")

    # Retrieve relevant chunks
    chunks = retriever.retrieve(question, top_k=top_k)

    if not chunks:
        click.echo("No relevant documentation found.")
        return

    # Generate answer
    answer = generator.generate(question, chunks, history=None)

    click.echo(f"💡 Answer:\n{answer.content}\n")
    click.echo(f"📊 Confidence: {answer.confidence:.0%}")

    if answer.sources:
        click.echo("📖 Sources:")
        for source in answer.sources:
            click.echo(f"  • {source.name}")


# Maximum number of conversation exchanges to keep in history
MAX_HISTORY_LENGTH = 5


@cli.command()
@click.option("--persist-dir", "-p", default=".data/doc_assistant", help="Directory where index is stored")
@click.option("--top-k", default=5, help="Number of chunks to retrieve")
@click.option("--model", "-m", default="claude-sonnet-4-20250514", help="Claude model to use")
def chat(persist_dir: str, top_k: int, model: str) -> None:
    """Start an interactive chat session with conversation history."""
    persist_path = Path(persist_dir)

    if not persist_path.exists():
        click.echo("❌ No index found. Run 'index' command first.", err=True)
        raise SystemExit(1)

    # Initialize components
    manager = IndexManager(persist_dir=persist_path)
    retriever = Retriever(index_manager=manager)
    generator = AnswerGenerator(model=model)

    click.echo("💬 Interactive chat (type 'exit' to quit)\n")

    # ARCH-2: Conversation history - list of (question, answer) tuples
    history: list[tuple[str, str]] = []

    while True:
        try:
            question = click.prompt("You", type=str)

            if question.lower() in ("exit", "quit", "q"):
                click.echo("Goodbye!")
                break

            # Retrieve and answer
            chunks = retriever.retrieve(question, top_k=top_k)

            # IMP-2: Provide feedback when no relevant chunks are found
            if not chunks:
                click.echo("\nNo relevant documentation found.\n")
                continue

            # Pass history to generator for multi-turn context
            answer = generator.generate(question, chunks, history=history if history else None)

            click.echo(f"\n💡 {answer.content}\n")
            click.echo(f"📊 Confidence: {answer.confidence:.0%}")

            if answer.sources:
                click.echo(f"📖 Sources: {', '.join(s.name for s in answer.sources)}\n")

            # Add to history, keeping only last MAX_HISTORY_LENGTH exchanges
            history.append((question, answer.content))
            if len(history) > MAX_HISTORY_LENGTH:
                history = history[-MAX_HISTORY_LENGTH:]

        except KeyboardInterrupt:
            click.echo("\nGoodbye!")
            break


@cli.command()
@click.option("--persist-dir", "-p", default=".data/doc_assistant", help="Directory where index is stored")
def stats(persist_dir: str) -> None:
    """Show comprehensive statistics about the indexed documentation."""
    persist_path = Path(persist_dir)

    if not persist_path.exists():
        click.echo("❌ No index found. Run 'index' command first.", err=True)
        raise SystemExit(1)

    manager = IndexManager(persist_dir=persist_path)
    stats = manager.get_stats()

    click.echo("\n📊 Index Statistics:")
    click.echo(f"  Chunks indexed: {stats['chunk_count']}")
    click.echo(f"  Sources indexed: {len(stats['sources'])}")
    click.echo(f"  Total size: {_format_size(stats['total_size_bytes'])}")
    click.echo(f"  Last modified: {stats['last_modified'] or 'N/A'}")
    click.echo(f"  Embedding model: {stats['embedding_model']}")
    click.echo(f"  Index location: {persist_path}")

    if stats["sources"]:
        click.echo("\n📁 Indexed files:")
        for source in stats["sources"][:10]:  # Show first 10
            click.echo(f"  • {Path(source).name}")
        if len(stats["sources"]) > 10:
            click.echo(f"  ... and {len(stats['sources']) - 10} more")


def _format_size(size_bytes: int) -> str:
    """Format size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


if __name__ == "__main__":
    cli()
