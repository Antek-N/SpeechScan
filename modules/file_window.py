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


class FileWindow(QDialog):
    """FileWindow is a class that loads GUI, retrieves mp3 file from user, counts the words in it and displays it.

        FileWindow class performs the following tasks:
        -loading FileWindow GUI
        -retrieving file path from user
        -checking if the file exist
        -checking if the file is in MP3 format
        -send audio file to count word occurrences in new thread
        -displaying the results of count.
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

        :param widgets: stacked program widgets
        :return: None
        """
        super().__init__()

        # Load UI layout from file_window.ui (Qt Designer .ui file)
        loadUi("views/file_window.ui", self)

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

    def choose_file(self) -> None:
        """
        Opens a file dialog box to allow the user to choose an MP3 file, and sets the file path
        field with the chosen file.

        :param: None
        :return: None
        """
        # Configure file dialog options (read-only, force Qt dialog instead of native)
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        options |= QFileDialog.DontUseNativeDialog

        # Show file chooser restricted to MP3 files
        file_path, _ = QFileDialog.getOpenFileName(self, "Choose file", "", "MP3 Files (*.mp3)", options=options)

        # If a file was selected, update the input field
        if file_path:
            self.file_path_field.setText(file_path)

    def submit(self) -> Union[None, int]:
        """Submits the count_button

        Retrieves the chosen file and sends it to the count_words function in the count_words.py
        to count word occurrences in new thread (by using count.words_thread.py) and after that display the
        results (words with number of occurrences) on the screen.

        :param: None
        :return: None if no error occurs, 0 otherwise
        """
        # Reset GUI elements to a clean state (clear errors, clear results table)
        self.reset_window_to_default()

        # Get file path entered/selected by user
        file_path = self.file_path_field.text()

        # Validate: check if file exists
        if not self.check_file_existence(file_path):
            self.display_error_message("file doesn't exist")
            return 0

        # Validate: check if file has .mp3 extension
        if not self.check_if_file_is_mp3(file_path):
            self.display_error_message("file must be in mp3 format")
            return 0

        try:
            # Retrieve API key entered by user
            api_key = self.api_key_field.text()

            # Prevent duplicate clicks while processing
            self.count_button.setEnabled(False)

            # Show animated loading spinner
            self.start_loading_animation()

            # Update button text to indicate counting in progress
            self.change_count_button_text(True)

            # Start worker thread that will handle transcription & counting
            self.start_words_counting_in_new_thread(api_key, file_path)

        except Exception as ex:
            # Log unexpected errors (e.g. threading, API, UI issues)
            logging.warning(ex)
            # Show generic error message in the UI
            self.display_error_message("Unknown problem encountered")

    def reset_window_to_default(self) -> None:
        """
        Clears the words table widget to remove any previous results and reset error text to default.

        :param: None
        :return: None
        """
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
        Checks if a file exists.

        :param file_path: the path to the chosen file
        :return: True if the file exists, False otherwise
        """
        # Use os.path.exists to validate the file path
        if os.path.exists(file_path):
            return True
        else:
            return False

    @staticmethod
    def check_if_file_is_mp3(file_path: str) -> bool:
        """
        Checks if a file is in MP3 format.

        :param file_path: the path to the chosen file
        :return: True if the file is in MP3 format, False otherwise
        """
        # Split file path into (basename, extension)
        _, extension = os.path.splitext(file_path)

        # Accept only files with .mp3 extension
        if extension == ".mp3":
            return True
        else:
            return False

    def start_loading_animation(self) -> None:
        """
        Starts the loading animation when counting the words.

        :param: None
        :return: None
        """
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
        Stops the loading animation when the word count is finished.

        :param: None
        :return: None
        """
        # Stop the currently running animation
        self.loading_widget.movie().stop()

        # Clear the label so no static frame remains
        self.loading_widget.clear()

    def change_count_button_text(self, is_counting: bool) -> None:
        """
        Changes the text on the count_button depending on the current state of counting.

        :param is_counting: True if counting is in progress, False otherwise
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
        Starts a new thread for counting the words in the given file.

        :param api_key: the API key for AssemblyAI
        :param file_path: the path to the audio file
        :return: None
        """
        # Create background thread responsible for transcription + word counting
        self.count_thread = modules.count_words_thread.CountWordsThread(file_path, api_key)

        # Connect thread's finished signal → handler that updates UI with results
        self.count_thread.finished.connect(self.handle_finished_counting_words)

        # Launch the worker thread (runs in parallel without freezing GUI)
        self.count_thread.start()

    def handle_finished_counting_words(self, counted_words_list: Union[list, str]) -> None:
        """
        Handles the finished event of the CountWordsThread, which emits the result of counting words in an MP3 file.
        If the result is an error message, displays the error message on the screen. Otherwise, sets up a table widget
        with the counted words list and displays it on the screen. Finally, stops the loading animation and changes the
        text in the count_button to "Count".

        :param counted_words_list: list of tuples, each tuple contains a word and its count in the form (word, count)
        or message with error (str)
        :return: None
        """
        # Handle known error messages returned by worker thread
        if counted_words_list in ["invalid api key", "file transcription error"]:
            self.display_error_message(counted_words_list)
        else:
            # Otherwise update table with counted words
            self.set_table_and_display_counted_words(counted_words_list)

        # Restore button text back to "Count"
        self.change_count_button_text(False)

        # Re-enable button after work finishes
        self.count_button.setEnabled(True)

        # Stop loading animation (spinner disappears)
        self.stop_loading_animation()

    def set_table_and_display_counted_words(self, counted_words_list: list) -> None:
        """
        Sets a table widget (by using set_table method) and displays the counted and sorted words with their counts.

        :param counted_words_list: list of tuples, each tuple contains a word and its count in the form (word, count)
        :return: None
        """
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

    def set_table(self, counted_words_list: list) -> None:
        """
        Sets the number of columns and rows in the table, sets column headers, and makes the table elements
        uneditable (set_table_and_display_counted_words sub-method).

        :param counted_words_list: list of tuples, each tuple contains a word and its count in the form (word, count)
        :return: None
        """
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
        Displays an error message if an error occurs during transcription.

        :param error_code: error code indicating the type of error
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

        # Display the message in red in the error widget
        self.error_widget.setStyleSheet("color: rgb(200, 0, 0);")
        self.error_widget.setText(message)
