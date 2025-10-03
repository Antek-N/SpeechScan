import logging

from PyQt5.QtWidgets import QDialog, QPushButton, QStackedWidget
from PyQt5.uic import loadUi  # type: ignore[import]

from speechscan.utils.paths import base_dir

log = logging.getLogger(__name__)

UI_DIR = base_dir() / "ui" / "views"  # ui/views directory


class StartWindow(QDialog):
    """
    Load and display the start window GUI.
    """

    file_button: QPushButton
    youtube_button: QPushButton

    def __init__(self, widgets: QStackedWidget) -> None:
        """
        Initialize the StartWindow and load user interface.

        :param widgets: Stacked program widgets.
        :return: None
        """
        super().__init__()
        # Load the UI layout from .ui file generated in Qt Designer
        loadUi(str(UI_DIR / "open_window.ui"), self)
        log.debug("UI loaded from %s", UI_DIR / "open_window.ui")

        # When "file button" is clicked, switch to the file selection view (index 1)
        self.file_button.clicked.connect(lambda: widgets.setCurrentIndex(1))  # type: ignore[attr-defined]  #...
        # ...created dynamically by loadUi, Qt signal has .connect()

        # When "YouTube" button is clicked, switch to the YouTube link view (index 2)
        self.youtube_button.clicked.connect(lambda: widgets.setCurrentIndex(2))  # type: ignore[attr-defined]  #...
        # ...created dynamically by loadUi, Qt signal has .connect()

        log.info("StartWindow initialized")
