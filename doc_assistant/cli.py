"""CLI interface for documentation assistant."""

from pathlib import Path

import click

from .answerer.core import AnswerGenerator
from .chunker.core import TextChunker
from .indexer.core import IndexManager
from .loader.core import DocumentLoader
from .retriever.core import Retriever


@click.group()
@click.version_option(version="0.1.0", prog_name="doc-assistant")
def cli() -> None:
    """Internal Developer Docs Assistant - Query your documentation in natural language."""
    pass


@cli.command()
@click.option("--docs", "-d", required=True, type=click.Path(exists=True), help="Directory containing documentation")
@click.option("--persist-dir", "-p", default=".data/doc_assistant", help="Directory to store index")
@click.option("--chunk-size", default=1000, help="Chunk size in characters")
@click.option("--overlap", default=200, help="Chunk overlap in characters")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--force", "-f", is_flag=True, help="Force full re-index (ignore existing index)")
def index(docs: str, persist_dir: str, chunk_size: int, overlap: int, verbose: bool, force: bool) -> None:
    """Index documents for querying.

    By default, performs incremental indexing - only re-indexing changed files.
    Use --force to perform a full re-index.
    """
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
        force = True  # Already true, but keep for clarity

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
                # Changed file
                if verbose:
                    click.echo(f"  Updated: {doc.source.name}")
                chunks = chunker.chunk(doc)
                manager.upsert_chunks(chunks)
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
        click.echo(f"\n✅ Index updated:")
        click.echo(f"   {new_count} new ({total_new_chunks} chunks)")
        click.echo(f"   {updated_count} updated ({total_updated_chunks} chunks)")
        click.echo(f"   {unchanged_count} unchanged")
        click.echo(f"   {removed_count} removed")

    click.echo(f"   Index stored in: {persist_path}")


@cli.command()
@click.option("--docs", "-d", required=True, type=click.Path(exists=True), help="Directory containing documentation")
@click.option("--persist-dir", "-p", default=".data/doc_assistant", help="Directory where index is stored")
@click.option("--top-k", default=5, help="Number of chunks to retrieve")
@click.argument("question")
def query(docs: str, persist_dir: str, top_k: int, question: str) -> None:
    """Query the documentation with a question."""
    persist_path = Path(persist_dir)

    if not persist_path.exists():
        click.echo("❌ No index found. Run 'index' command first.", err=True)
        raise SystemExit(1)

    # Initialize components
    manager = IndexManager(persist_dir=persist_path)
    retriever = Retriever(index_manager=manager)
    generator = AnswerGenerator()

    click.echo(f"\n❓ Question: {question}\n")

    # Retrieve relevant chunks
    chunks = retriever.retrieve(question, top_k=top_k)

    if not chunks:
        click.echo("No relevant documentation found.")
        return

    # Generate answer
    answer = generator.generate(question, chunks)

    click.echo(f"💡 Answer:\n{answer.content}\n")
    click.echo(f"📊 Confidence: {answer.confidence:.0%}")

    if answer.sources:
        click.echo("📖 Sources:")
        for source in answer.sources:
            click.echo(f"  • {source.name}")


@cli.command()
@click.option("--docs", "-d", required=True, type=click.Path(exists=True), help="Directory containing documentation")
@click.option("--persist-dir", "-p", default=".data/doc_assistant", help="Directory where index is stored")
@click.option("--top-k", default=5, help="Number of chunks to retrieve")
def chat(docs: str, persist_dir: str, top_k: int) -> None:
    """Start an interactive chat session."""
    persist_path = Path(persist_dir)

    if not persist_path.exists():
        click.echo("❌ No index found. Run 'index' command first.", err=True)
        raise SystemExit(1)

    # Initialize components
    manager = IndexManager(persist_dir=persist_path)
    retriever = Retriever(index_manager=manager)
    generator = AnswerGenerator()

    click.echo("💬 Interactive chat (type 'exit' to quit)\n")

    while True:
        try:
            question = click.prompt("You", type=str)

            if question.lower() in ("exit", "quit", "q"):
                click.echo("Goodbye!")
                break

            # Retrieve and answer
            chunks = retriever.retrieve(question, top_k=top_k)
            answer = generator.generate(question, chunks)

            click.echo(f"\n💡 {answer.content}\n")
            click.echo(f"📊 Confidence: {answer.confidence:.0%}")

            if answer.sources:
                click.echo(f"📖 Sources: {', '.join(s.name for s in answer.sources)}\n")

        except KeyboardInterrupt:
            click.echo("\nGoodbye!")
            break


@cli.command()
@click.option("--persist-dir", "-p", default=".data/doc_assistant", help="Directory where index is stored")
def stats(persist_dir: str) -> None:
    """Show statistics about the indexed documentation."""
    persist_path = Path(persist_dir)

    if not persist_path.exists():
        click.echo("❌ No index found. Run 'index' command first.", err=True)
        raise SystemExit(1)

    manager = IndexManager(persist_dir=persist_path)
    count = manager.count()

    click.echo("\n📊 Index Statistics:")
    click.echo(f"  Chunks indexed: {count}")
    click.echo(f"  Index location: {persist_path}")


if __name__ == "__main__":
    cli()
