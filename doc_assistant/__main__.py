"""Entry point for running as a standalone package module."""

from .cli import cli


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
