"""Entry point for voice-to-text CLI."""

from .cli import CLI


def main():
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()
