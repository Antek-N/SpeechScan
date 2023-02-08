from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi


class StartWindow(QDialog):
    """StartWindow is a class that loads start window GUI"""
    def __init__(self, widgets):
        super().__init__()
        # Load UI
        loadUi("views/open_window.ui", self)
        # Go to the file_window after clicking the File button
        self.file_button.clicked.connect(lambda: widgets.setCurrentIndex(1))
        # Go to the youtube_window after clicking the YouTube button
        self.youtube_button.clicked.connect(lambda: widgets.setCurrentIndex(2))
