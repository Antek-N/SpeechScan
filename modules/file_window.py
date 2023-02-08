from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi


class FileWindow(QDialog):
    def __init__(self, widgets):
        super().__init__()
        # Load user interface
        loadUi("views/file_window.ui", self)
        # Return to the start_window after clicking the Cancel button
        self.cancel_button.clicked.connect(lambda: widgets.setCurrentIndex(0))
