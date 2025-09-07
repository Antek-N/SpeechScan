import sys
from pathlib import Path

from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

import modules.file_window
import modules.start_window
import modules.youtube_window


class App:
    """App is a main class of application"""
    def __init__(self):
        """
        Initializes the application object.
        Creates QStackedWidget and adds the windows (Start, File, YouTube) to it.
        Displays the stacket widget.
        Exits the application at the end of the Qt event loop.
        """
        # Create the Qt application instance
        app = QApplication(sys.argv)

        # Load application stylesheet from .qss
        app.setStyleSheet(Path('style/style.qss').read_text())

        # Create a container that can switch between multiple pages
        widgets = QtWidgets.QStackedWidget()

        # Set application name and window icon
        app.setApplicationName("SpeechScan")
        app.setWindowIcon(QIcon('img/icon.png'))

        # Instantiate pages, passing the stacked widget for navigation
        start_window = modules.start_window.StartWindow(widgets)
        file_window = modules.file_window.FileWindow(widgets)
        youtube_window = modules.youtube_window.YouTubeWindow(widgets)

        # Add pages to the stacked widget (index order matters for navigation)
        widgets.addWidget(start_window)  # index 0 -> Start
        widgets.addWidget(file_window)  # index 1 -> File
        widgets.addWidget(youtube_window)  # index 2 -> YouTube

        # Fix the window size for the entire stacked widget
        widgets.setFixedSize(400, 500)

        # Show the main window
        widgets.show()

        # Start the Qt event loop and exit the process when it ends
        sys.exit(app.exec_())


if __name__ == '__main__':
    App()
