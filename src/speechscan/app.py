import logging
import sys

from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from speechscan.ui.file_window import FileWindow
from speechscan.ui.start_window import StartWindow
from speechscan.ui.youtube_window import YouTubeWindow
from speechscan.utils.paths import base_dir

log = logging.getLogger(__name__)

ASSETS_DIR = base_dir() / "assets"  # assets directory


class App:
    """
    Application entry point
    """

    def __init__(self) -> None:
        """
        Initialize and run the Qt application:
        create the stacked widget, add windows (Start, File, YouTube),
        show the UI, and start the event loop via run().

        :return: None
        """
        # Create the Qt application instance
        self.app = QApplication(sys.argv)
        log.debug("QApplication created")

        # Load application stylesheet from .qss
        self._load_stylesheet()

        # Build and show the UI
        self._build_ui()

    def _load_stylesheet(self) -> None:
        """
        Load the application stylesheet from the assets' directory.

        :return: None
        """
        try:
            self.app.setStyleSheet((ASSETS_DIR / "style" / "style.qss").read_text(encoding="utf-8"))
            log.debug("Stylesheet loaded from %s", ASSETS_DIR / "style" / "style.qss")
        except Exception as ex:
            log.error("Failed to load stylesheet: %s", ex)
            raise

    def _build_ui(self) -> None:
        """
        Build the stacked widget, add windows, and show the main window.

        :return: None
        """
        # Create a container that can switch between multiple pages
        self.widgets = QtWidgets.QStackedWidget()
        log.debug("QStackedWidget created")

        # Set application name and window icon
        self.app.setApplicationName("SpeechScan")
        self.app.setWindowIcon(QIcon(str(ASSETS_DIR / "img" / "icon.png")))
        log.debug("Application name and icon set")

        # Instantiate pages, passing the stacked widget for navigation
        start_window = StartWindow(self.widgets)
        file_window = FileWindow(self.widgets)
        youtube_window = YouTubeWindow(self.widgets)
        log.debug("Windows instantiated: StartWindow, FileWindow, YouTubeWindow")

        # Add pages to the stacked widget (index order matters for navigation)
        self.widgets.addWidget(start_window)  # index 0 -> Start
        self.widgets.addWidget(file_window)  # index 1 -> File
        self.widgets.addWidget(youtube_window)  # index 2 -> YouTube
        log.debug("Windows added to stacked widget (indices 0,1,2)")

        # Fix the window size for the entire stacked widget
        self.widgets.setFixedSize(400, 500)
        log.debug("Fixed window size set to 400x500")

        # Show the main window
        self.widgets.show()
        log.info("Main window shown")

    def run(self) -> int:
        """
        Start the Qt event loop and return its exit code.

        :return: Int, Qt event loop exit code.
        """
        log.info("Starting Qt event loop")
        return self.app.exec_()
