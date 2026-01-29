"""ASUS Helper - Power management tool for ASUS laptops on Linux."""

__version__ = "0.1.0"


def main() -> None:
    """Entry point for the application."""
    from asus_helper.app import run_app
    run_app()
