import os
import logging
from typing import Union
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QAbstractItemView, QHeaderView, QFileDialog
from PyQt5.uic import loadUi
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
    def __init__(self, widgets) -> None:
        """
        Initialize the FileWindow and load user interface.

        :param widgets: stacked program widgets
        :return: None
        """
        super().__init__()
        # Load user interface
        loadUi("views/file_window.ui", self)
        self.browse_button.clicked.connect(self.choose_file)
        self.count_button.clicked.connect(self.submit)
        # Return to the start_window after clicking the Cancel button
        self.cancel_button.clicked.connect(lambda: widgets.setCurrentIndex(0))
        self.count_thread = None

    def choose_file(self) -> None:
        """
        Opens a file dialog box to allow the user to choose an MP3 file, and sets the file path
        field with the chosen file.

        :param: None
        :return: None
        """
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        options |= QFileDialog.DontUseNativeDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Choose file", "", "MP3 Files (*.mp3)", options=options)

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
        self.reset_window_to_default()

        file_path = self.file_path_field.text()

        if not self.check_file_existence(file_path):
            # Display error if the file doesn't exist
            self.display_error_message("file doesn't exist")
            return 0

        if not self.check_if_file_is_mp3(file_path):
            # Display error if the file is not in mp3 format
            self.display_error_message("file must be in mp3 format")
            return 0

        try:
            # Retrieve the API key from the text field and count the words using count_words.py
            api_key = self.api_key_field.text()
            self.count_button.setEnabled(False)  # Disable the count_button
            self.start_loading_animation()
            self.change_count_button_text(True)
            self.start_words_counting_in_new_thread(api_key, file_path)

        except Exception as ex:
            logging.warning(ex)

    def reset_window_to_default(self) -> None:
        """
        Clears the words table widget to remove any previous results and reset error text to default.

        :param: None
        :return: None
        """
        # Reset the error widget by setting its style sheet and text to default values
        self.error_widget.setStyleSheet("color: rgb(0, 0, 0);")
        self.error_widget.setText("==============")
        # Clear the words table widget to remove any previous results
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
        _, extension = os.path.splitext(file_path)
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
        loading_movie = QMovie("img/loading.gif")
        self.loading_widget.setMovie(loading_movie)
        self.loading_widget.setScaledContents(True)
        loading_movie.start()

    def stop_loading_animation(self) -> None:
        """
        Stops the loading animation when the word count is finished.

        :param: None
        :return: None
        """
        self.loading_widget.movie().stop()
        self.loading_widget.clear()

    def change_count_button_text(self, is_counting: bool) -> None:
        """
        Changes the text on the count_button depending on the current state of counting.

        :param is_counting: True if counting is in progress, False otherwise
        :return: None
        """
        if is_counting:
            self.count_button.setText("Counting...")
        else:
            self.count_button.setText("Count")

    def start_words_counting_in_new_thread(self, api_key: str, file_path: str) -> None:
        """
        Starts a new thread for counting the words in the given file.

        :param api_key: the API key for AssemblyAI
        :param file_path: the path to the audio file
        :return: None
        """
        self.count_thread = modules.count_words_thread.CountWordsThread(file_path, api_key)
        self.count_thread.finished.connect(self.handle_finished_counting_words)
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
        if counted_words_list in ["invalid api key", "file transcription error"]:
            # Display the error message if API key or file transcription is invalid
            self.display_error_message(counted_words_list)
        else:
            # Else set table and display counted words list
            self.set_table_and_display_counted_words(counted_words_list)
        self.change_count_button_text(False)
        self.count_button.setEnabled(True)  # Re-enable the count_button
        self.stop_loading_animation()

    def set_table_and_display_counted_words(self, counted_words_list: list) -> None:
        """
        Sets a table widget (by using set_table method) and displays the counted and sorted words with their counts.

        :param counted_words_list: list of tuples, each tuple contains a word and its count in the form (word, count)
        :return: None
        """
        self.set_table(counted_words_list)
        for i, word in enumerate(counted_words_list):
            # Set word
            item = QtWidgets.QTableWidgetItem(word[0])
            self.words_table_widget.setItem(i, 0, item)
            # Set count
            item = QtWidgets.QTableWidgetItem(str(word[1]))
            self.words_table_widget.setItem(i, 1, item)

    def set_table(self, counted_words_list: list) -> None:
        """
        Sets the number of columns and rows in the table, sets column headers, and makes the table elements
        uneditable (set_table_and_display_counted_words sub-method).

        :param counted_words_list: list of tuples, each tuple contains a word and its count in the form (word, count)
        :return: None
        """
        self.words_table_widget.setRowCount(len(counted_words_list))
        self.words_table_widget.setColumnCount(2)
        self.words_table_widget.setHorizontalHeaderLabels(["Word", "Repetitions"])
        self.words_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.words_table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def display_error_message(self, error_code: str) -> None:
        """
        Displays an error message if an error occurs during transcription.

        :param error_code: error code indicating the type of error
        :return: None
        """
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
        self.error_widget.setStyleSheet("color: rgb(200, 0, 0);")
        self.error_widget.setText(message)
