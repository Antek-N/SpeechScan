import os
import logging
from typing import Union

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QDialog,
    QPushButton,
    QLineEdit,
    QLabel,
    QTableWidget,
    QAbstractItemView,
    QHeaderView,
    QFileDialog,
)
from PyQt5.uic import loadUi  # type: ignore[import]
from PyQt5.QtGui import QMovie

import modules.count_words_thread

log = logging.getLogger(__name__)


class FileWindow(QDialog):
    """
    Load GUI, retrieve MP3 file from user, count words in it, and display results.
    """

    # GUI element references (populated dynamically by loadUi)
    browse_button: QPushButton
    count_button: QPushButton
    back_button: QPushButton
    file_path_field: QLineEdit
    api_key_field: QLineEdit
    error_widget: QLabel
    loading_widget: QLabel
    words_table_widget: QTableWidget

    def __init__(self, widgets) -> None:
        """
        Initialize the FileWindow and load user interface.

        :param widgets: Stacked program widgets.
        :return: None
        """
        super().__init__()

        # Load UI layout from file_window.ui (Qt Designer .ui file)
        loadUi("views/file_window.ui", self)
        log.debug("UI loaded from views/file_window.ui")

        # Connect "Browse" button - open file chooser
        self.browse_button.clicked.connect(self.choose_file)  # type: ignore[attr-defined]  #...
        # ...created dynamically by loadUi, Qt signal has .connect()

        # Connect "Count" button - start processing and word counting
        self.count_button.clicked.connect(self.submit)  # type: ignore[attr-defined]  #...
        # ...created dynamically by loadUi, Qt signal has .connect()

        # Connect "Back" button - return to start window (index 0 in stacked widgets)
        self.back_button.clicked.connect(lambda: widgets.setCurrentIndex(0))  # type: ignore[attr-defined]  #...
        # ...created dynamically by loadUi, Qt signal has .connect()

        # Placeholder for worker thread (word counting)
        self.count_thread = None
        log.debug("FileWindow initialized")

    def choose_file(self) -> None:
        """
        Open a file dialog for selecting an MP3 file and update the path field.

        :param: None
        :return: None
        """
        log.info("Opening file dialog for MP3 selection")
        # Configure file dialog options (read-only, force Qt dialog instead of native)
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        options |= QFileDialog.DontUseNativeDialog

        # Show file chooser restricted to MP3 files
        file_path, _ = QFileDialog.getOpenFileName(self, "Choose file", "", "MP3 Files (*.mp3)", options=options)
        log.debug("File dialog returned path: %s", file_path if file_path else "(none)")

        # If a file was selected, update the input field
        if file_path:
            self.file_path_field.setText(file_path)
            log.info("Selected file set to: %s", file_path)

    def submit(self) -> Union[None, int]:
        """
        Handle count_button click: validate file, start counting, and update UI.

        :param: None
        :return: None if no error occurs, 0 otherwise.
        """
        log.info("Submit clicked: starting validation and counting")
        # Reset GUI elements to a clean state (clear errors, clear results table)
        self.reset_window_to_default()

        # Get file path entered/selected by user
        file_path = self.file_path_field.text()
        log.debug("User-provided file path: %s", file_path)

        # Validate: check if file exists
        if not self.check_file_existence(file_path):
            log.warning("File does not exist: %s", file_path)
            self.display_error_message("file doesn't exist")
            return 0

        # Validate: check if file has .mp3 extension
        if not self.check_if_file_is_mp3(file_path):
            log.warning("Invalid file extension (not .mp3): %s", file_path)
            self.display_error_message("file must be in mp3 format")
            return 0

        try:
            # Retrieve API key entered by user
            api_key = self.api_key_field.text()
            log.debug("API key length: %d", len(api_key) if isinstance(api_key, str) else -1)

            # Prevent duplicate clicks while processing
            self.count_button.setEnabled(False)
            log.debug("count_button disabled during processing")

            # Show animated loading spinner
            self.start_loading_animation()

            # Update button text to indicate counting in progress
            self.change_count_button_text(True)

            # Start worker thread that will handle transcription & counting
            self.start_words_counting_in_new_thread(api_key, file_path)
            log.info("Counting thread started")

        except Exception as ex:
            # Log unexpected errors (e.g. threading, API, UI issues)
            logging.warning(ex)
            log.error("Unexpected error during submit: %s", ex)
            # Show generic error message in the UI
            self.display_error_message("Unknown problem encountered")

    def reset_window_to_default(self) -> None:
        """
        Reset the window: clear results table and reset error message.

        :param: None
        :return: None
        """
        log.debug("Resetting window to default state")
        # Reset error label to neutral (gray) style and placeholder text
        self.error_widget.setStyleSheet("color: rgb(177, 177, 177);")
        self.error_widget.setText("==============")

        # Completely clear results table (remove headers, rows, and data)
        self.words_table_widget.clear()
        self.words_table_widget.setRowCount(0)
        self.words_table_widget.setColumnCount(0)

    @staticmethod
    def check_file_existence(file_path: str) -> bool:
        """
        Check if a file exists.

        :param file_path: Path to the chosen file.
        :return: True if the file exists, False otherwise.
        """
        # Use os.path.exists to validate the file path
        exists = os.path.exists(file_path)
        if exists:
            logging.getLogger(__name__).debug("File exists: %s", file_path)
            return True
        else:
            logging.getLogger(__name__).debug("File does not exist: %s", file_path)
            return False

    @staticmethod
    def check_if_file_is_mp3(file_path: str) -> bool:
        """
        Check if a file has .mp3 extension.

        :param file_path: Path to the chosen file.
        :return: True if file extension is .mp3, False otherwise.
        """
        # Split file path into (basename, extension)
        _, extension = os.path.splitext(file_path)

        # Accept only files with .mp3 extension
        if extension == ".mp3":
            logging.getLogger(__name__).debug("File has .mp3 extension: %s", file_path)
            return True
        else:
            logging.getLogger(__name__).debug("File extension not .mp3: %s (ext=%s)", file_path, extension)
            return False

    def start_loading_animation(self) -> None:
        """
        Start the loading animation while counting words.

        :param: None
        :return: None
        """
        log.debug("Starting loading animation")
        # Load animated GIF for the "loading" indicator
        loading_movie = QMovie("img/loading.gif")

        # Assign animation to the QLabel widget
        self.loading_widget.setMovie(loading_movie)

        # Scale GIF to fit the label dimensions
        self.loading_widget.setScaledContents(True)

        # Start playing the animation
        loading_movie.start()

    def stop_loading_animation(self) -> None:
        """
        Stop the loading animation when counting is finished.

        :param: None
        :return: None
        """
        log.debug("Stopping loading animation")
        # Stop the currently running animation
        self.loading_widget.movie().stop()

        # Clear the label so no static frame remains
        self.loading_widget.clear()

    def change_count_button_text(self, is_counting: bool) -> None:
        """
        Update the count_button text depending on state.

        :param is_counting: True if counting is in progress, False otherwise.
        :return: None
        """
        # Show "Counting..." while background thread is active
        if is_counting:
            self.count_button.setText("Counting...")
        # Restore default label when counting is done
        else:
            self.count_button.setText("Count")

    def start_words_counting_in_new_thread(self, api_key: str, file_path: str) -> None:
        """
        Start a new thread for counting words in the given file.

        :param api_key: API key for AssemblyAI.
        :param file_path: Path to the audio file.
        :return: None
        """
        log.debug("Initializing CountWordsThread with file_path=%s", file_path)
        # Create background thread responsible for transcription + word counting
        self.count_thread = modules.count_words_thread.CountWordsThread(file_path, api_key)

        # Connect thread's finished signal → handler that updates UI with results
        self.count_thread.finished.connect(self.handle_finished_counting_words)
        log.debug("Connected CountWordsThread.finished to handler")

        # Launch the worker thread (runs in parallel without freezing GUI)
        self.count_thread.start()
        log.info("CountWordsThread started")

    def handle_finished_counting_words(self, counted_words_list: Union[list, str]) -> None:
        """
        Handle CountWordsThread finished signal and update UI with results.

        :param counted_words_list: Word count list [(word, count)] or error message.
        :return: None
        """
        log.info("Received finished signal with result type: %s", type(counted_words_list).__name__)
        # Handle known error messages returned by worker thread
        if counted_words_list in ["invalid api key", "file transcription error"]:
            log.warning("Counting failed with error: %s", counted_words_list)
            self.display_error_message(counted_words_list)
        else:
            # Otherwise update table with counted words
            log.info("Displaying counted words (%d rows)", len(counted_words_list))
            self.set_table_and_display_counted_words(counted_words_list)

        # Restore button text back to "Count"
        self.change_count_button_text(False)

        # Re-enable button after work finishes
        self.count_button.setEnabled(True)
        log.debug("count_button re-enabled")

        # Stop loading animation (spinner disappears)
        self.stop_loading_animation()

    def set_table_and_display_counted_words(self, counted_words_list: list) -> None:
        """
        Set up the table widget and display counted words.

        :param counted_words_list: List of (word, count) tuples.
        :return: None
        """
        log.debug("Setting table and displaying %d counted words", len(counted_words_list))
        # Prepare table (set rows, columns, headers, resize mode, disable editing)
        self.set_table(counted_words_list)

        # Populate table with words and counts
        for i, word in enumerate(counted_words_list):
            # Column 0 → word
            item = QtWidgets.QTableWidgetItem(word[0])
            self.words_table_widget.setItem(i, 0, item)

            # Column 1 → count
            item = QtWidgets.QTableWidgetItem(str(word[1]))
            self.words_table_widget.setItem(i, 1, item)
        log.info("Table populated with %d rows", len(counted_words_list))

    def set_table(self, counted_words_list: list) -> None:
        """
        Configure table: rows, columns, headers, and read-only settings.

        :param counted_words_list: List of (word, count) tuples.
        :return: None
        """
        log.debug("Configuring table for %d rows", len(counted_words_list))
        # Set the number of rows to match the number of items in results
        self.words_table_widget.setRowCount(len(counted_words_list))

        # Table always has 2 columns: word -> occurrence count
        self.words_table_widget.setColumnCount(2)

        # Define column headers
        self.words_table_widget.setHorizontalHeaderLabels(["Word", "Number of occurrences"])

        # Stretch columns to use the full table width
        self.words_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Make cells read-only
        self.words_table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def display_error_message(self, error_code: str) -> None:
        """
        Display an error message in the UI.

        :param error_code: Error code string.
        :return: None
        """
        # Translate error code into a user-friendly message
        if error_code == "file doesn't exist":
            message = "File doesn't exist"
        elif error_code == "file must be in mp3 format":
            message = "File must be in mp3 format"
        elif error_code == "invalid api key":
            message = "Invalid API key"
        elif error_code == "file transcription error":
            message = "File transcription problem encountered"
        else:
            message = "Unknown problem encountered"

        log.warning("Displaying error message: %s (code=%s)", message, error_code)

        # Display the message in red in the error widget
        self.error_widget.setStyleSheet("color: rgb(200, 0, 0);")
        self.error_widget.setText(message)
