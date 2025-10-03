import logging
import sys

from speechscan.app import App


def main() -> int:
    """
    Main entry point
    Configure logging, start the application, and return exit code.

    :return: None
    """
    # Configure logging system
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    log = logging.getLogger(__name__)
    log.debug("Logging configured")

    # Log application launch
    log.info("Launching application")

    # Create and run the App, return its exit code
    return App().run()


if __name__ == "__main__":
    # Exit with proper return code for OS
    sys.exit(main())
