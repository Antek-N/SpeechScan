import os
import logging
from typing import Union
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QAbstractItemView, QHeaderView, QFileDialog
from PyQt5.uic import loadUi
import modules.count_words


class FileWindow(QDialog):
    """FileWindow is a class that loads GUI, retrieves mp3 file from user, counts the words in it and displays it.

        FileWindow class performs the following tasks:
        -loading FileWindow GUI
        -retrieving file path from user
        -checking if the file exist
        -checking if the file is in MP3 format
        -send audio file to count word occurrences
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
        """
        Retrieves the chosen file and sends it to the count_words function in the count_words.py
        to count word occurrences and after that display the results (words with number of occurrences)
        on the screen.

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
            counted_words_list = modules.count_words.CountWords(file_path, api_key).count_words()

            if counted_words_list in ["invalid api key", "file transcription error"]:
                # Display the error message if API key or file transcription is invalid
                self.display_error_message(counted_words_list)
            else:
                # Else set table and display counted words list
                self.set_table_and_display_counted_words(counted_words_list)
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
    def check_file_existence(file_path) -> bool:
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
    def check_if_file_is_mp3(file_path) -> bool:
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

    def set_table_and_display_counted_words(self, counted_words_list: list) -> None:
        """
        Sets a table widget and displays the counted and sorted words with their counts.

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
