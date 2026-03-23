"""Tests for CLI commands."""

from pathlib import Path
from tempfile import TemporaryDirectory

from click.testing import CliRunner

from doc_assistant.cli import cli


def test_stats_command_no_index():
    """Test stats command when no index exists."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        result = runner.invoke(cli, ["stats", "-p", tmpdir])

        # The command succeeds but shows 0 chunks (IndexManager creates the index dir)
        assert result.exit_code == 0
        assert "Chunks indexed: 0" in result.output


def test_index_command_creates_index():
    """Test that index command creates an index from documents."""
    runner = CliRunner()

    with TemporaryDirectory() as docs_dir:
        # Create a test document
        test_doc = Path(docs_dir) / "test.md"
        test_doc.write_text("# Test Document\n\nThis is test content for indexing.")

        with TemporaryDirectory() as persist_dir:
            result = runner.invoke(
                cli,
                ["index", "-d", docs_dir, "-p", persist_dir],
            )

            assert result.exit_code == 0
            assert "Indexing documents" in result.output
            assert "Indexed" in result.output or "new" in result.output

            # Verify the index was created
            persist_path = Path(persist_dir)
            assert persist_path.exists()


def test_index_command_verbose_output():
    """Test that verbose flag shows detailed output."""
    runner = CliRunner()

    with TemporaryDirectory() as docs_dir:
        # Create a test document
        test_doc = Path(docs_dir) / "verbose.md"
        test_doc.write_text("# Verbose Test\n\nContent for verbose test.")

        with TemporaryDirectory() as persist_dir:
            result = runner.invoke(
                cli,
                ["index", "-d", docs_dir, "-p", persist_dir, "-v"],
            )

            assert result.exit_code == 0
            # Verbose should show processing details
            assert "Processing:" in result.output or "New:" in result.output


def test_index_command_force_reindex():
    """Test that --force flag performs full re-index."""
    runner = CliRunner()

    with TemporaryDirectory() as docs_dir:
        # Create a test document
        test_doc = Path(docs_dir) / "force.md"
        test_doc.write_text("# Force Test\n\nContent for force test.")

        with TemporaryDirectory() as persist_dir:
            # First index
            result1 = runner.invoke(
                cli,
                ["index", "-d", docs_dir, "-p", persist_dir],
            )
            assert result1.exit_code == 0

            # Force re-index
            result2 = runner.invoke(
                cli,
                ["index", "-d", docs_dir, "-p", persist_dir, "--force", "-v"],
            )
            assert result2.exit_code == 0
            assert "full re-index" in result2.output.lower() or "force" in result2.output.lower()


def test_index_command_invalid_overlap():
    """Test that overlap >= chunk-size produces an error."""
    runner = CliRunner()

    with TemporaryDirectory() as docs_dir:
        test_doc = Path(docs_dir) / "test.md"
        test_doc.write_text("Test content")

        with TemporaryDirectory() as persist_dir:
            result = runner.invoke(
                cli,
                ["index", "-d", docs_dir, "-p", persist_dir, "--chunk-size", "100", "--overlap", "100"],
            )

            assert result.exit_code == 1
            assert "overlap must be less than chunk-size" in result.output


def test_index_command_handles_nested_files():
    """Test that index command processes files in nested directories."""
    runner = CliRunner()

    with TemporaryDirectory() as docs_dir:
        # Create nested structure
        docs_path = Path(docs_dir)
        nested_dir = docs_path / "subdir" / "nested"
        nested_dir.mkdir(parents=True)

        (docs_path / "root.md").write_text("# Root Document")
        (nested_dir / "nested.md").write_text("# Nested Document")

        with TemporaryDirectory() as persist_dir:
            result = runner.invoke(
                cli,
                ["index", "-d", docs_dir, "-p", persist_dir, "-v"],
            )

            assert result.exit_code == 0
            # Should process both files
            assert "2 documents" in result.output or "2 new" in result.output or "root.md" in result.output


def test_stats_command_with_index():
    """Test stats command when index exists."""
    runner = CliRunner()

    with TemporaryDirectory() as docs_dir:
        test_doc = Path(docs_dir) / "stats.md"
        test_doc.write_text("# Stats Test\n\nContent for stats test.")

        with TemporaryDirectory() as persist_dir:
            # Create index first
            runner.invoke(cli, ["index", "-d", docs_dir, "-p", persist_dir])

            # Now test stats
            result = runner.invoke(cli, ["stats", "-p", persist_dir])

            assert result.exit_code == 0
            assert "Index Statistics" in result.output
            assert "Chunks indexed:" in result.output


def test_query_command_no_index():
    """Test query command when no index exists."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        result = runner.invoke(cli, ["query", "-p", tmpdir, "test question"])

        # The command succeeds but finds no relevant docs (IndexManager creates the index dir)
        assert result.exit_code == 0
        assert "No relevant documentation found" in result.output
