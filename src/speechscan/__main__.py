import logging
import sys

from speechscan.app import App
from speechscan.logging_config import configure_logging


def main() -> int:
    """
    Main entry point
    Configure logging, start the application, and return exit code.

    :return: None
    """
    # Configure logging system
    configure_logging()
    log = logging.getLogger(__name__)
    log.debug("Logging configured")

    # Log application launch
    log.info("Launching application")

    # Create and run the App, return its exit code
    return App().run()


if __name__ == "__main__":
    # Exit with proper return code for OS
    sys.exit(main())
