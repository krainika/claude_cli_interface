"""Entry point: python -m claude_tui"""

from claude_tui.app import ClaudeTUIApp


def main() -> None:
    app = ClaudeTUIApp()
    app.run()


if __name__ == "__main__":
    main()
