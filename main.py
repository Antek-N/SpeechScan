import sys
from PyQt5.QtGui import QIcon
from PyQt5 import QtWidgets
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
        # Create app
        app = QApplication(sys.argv)
        # Create stacked widget
        widgets = QtWidgets.QStackedWidget()

        # Set program title and icon
        app.setApplicationName("SpeechScan")
        app.setWindowIcon(QIcon('img/icon.png'))

        # Create windows
        start_window = modules.start_window.StartWindow(widgets)
        file_window = modules.file_window.FileWindow(widgets)
        youtube_window = modules.youtube_window.YouTubeWindow(widgets)

        # add windows to stacked widget
        widgets.addWidget(start_window)
        widgets.addWidget(file_window)
        widgets.addWidget(youtube_window)
        widgets.setFixedSize(400, 500)
        # Show the stacked widget
        widgets.show()
        # Exits the application at the end of the Qt event loop
        sys.exit(app.exec_())


if __name__ == '__main__':
    App()
