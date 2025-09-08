import logging
import sys
from pathlib import Path

from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from logging_config import configure_logging
import modules.file_window
import modules.start_window
import modules.youtube_window

configure_logging()
log = logging.getLogger(__name__)
log.debug("Logging configured")


class App:
    """
    Main application class.
    """
    def __init__(self):
        """
        Initialize and run the Qt application:
        create the stacked widget, add windows (Start, File, YouTube),
        show the UI, and start the event loop.

        :param: None
        :return: None
        """
        # Create the Qt application instance
        app = QApplication(sys.argv)
        log.debug("QApplication created")

        # Load application stylesheet from .qss
        try:
            app.setStyleSheet(Path('style/style.qss').read_text())
            log.debug("Stylesheet loaded from style/style.qss")
        except Exception as ex:
            log.error("Failed to load stylesheet: %s", ex)
            raise

        # Create a container that can switch between multiple pages
        widgets = QtWidgets.QStackedWidget()
        log.debug("QStackedWidget created")

        # Set application name and window icon
        app.setApplicationName("SpeechScan")
        app.setWindowIcon(QIcon('img/icon.png'))
        log.debug("Application name and icon set")

        # Instantiate pages, passing the stacked widget for navigation
        start_window = modules.start_window.StartWindow(widgets)
        file_window = modules.file_window.FileWindow(widgets)
        youtube_window = modules.youtube_window.YouTubeWindow(widgets)
        log.debug("Windows instantiated: StartWindow, FileWindow, YouTubeWindow")

        # Add pages to the stacked widget (index order matters for navigation)
        widgets.addWidget(start_window)  # index 0 -> Start
        widgets.addWidget(file_window)  # index 1 -> File
        widgets.addWidget(youtube_window)  # index 2 -> YouTube
        log.debug("Windows added to stacked widget (indices 0,1,2)")

        # Fix the window size for the entire stacked widget
        widgets.setFixedSize(400, 500)
        log.debug("Fixed window size set to 400x500")

        # Show the main window
        widgets.show()
        log.info("Main window shown")

        # Start the Qt event loop and exit the process when it ends
        log.info("Starting Qt event loop")
        sys.exit(app.exec_())


if __name__ == '__main__':
    log.info("Launching application")
    App()
