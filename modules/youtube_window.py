import os
import logging
from typing import Union
import urllib.request
import urllib.parse
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QAbstractItemView, QHeaderView
from PyQt5.uic import loadUi
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QMovie
from pytube import YouTube
import modules.count_words_thread
import modules.download_video_thread


class YouTubeWindow(QDialog):
    """YouTubeWindow is a class that loads GUI, downloads audio from YouTube, counts the words in it and displays it.

    YouTubeWindow class performs the following tasks:
    -loading YouTubeWindow GUI
    -checking the URL validity
    -checking if the video exists
    -setting the video title and thumbnail
    -downloading the audio
    -send audio file to count word occurrences in new thread
    -displaying the results of count.
    """
    def __init__(self, widgets):
        """
        Initialize the YoutubeWindow and load user interface.

        :param widgets: stacked program widgets.
        return: None
        """
        super().__init__()
        # Load user interface
        loadUi("views/youtube_window.ui", self)
        self.count_button.clicked.connect(self.submit)
        # Return to the start_window after clicking the Cancel button
        self.cancel_button.clicked.connect(lambda: widgets.setCurrentIndex(0))
        self.file_path = ""
        self.download_video_thread = None
        self.count_thread = None

    def submit(self) -> Union[None, int]:
        """Submits the count_button

        Submits the count_button and downloads the audio from the YouTube video. If the URL is valid, sets
        the video title and thumbnail, starts the loading animation, and changes the count_button text
        to "Counting...". The audio from YouTube video is downloaded as a temporary file in a new thread by calling
        the function start_download_video_in_new_thread. Then, the word counting is performed in a separate thread,
        and the results (words with number of occurrences) are displayed on the screen. Finally, the temporary file
        containing the audio is removed.

        :param: None
        :return: None if no error occurs, 0 otherwise
        """
        self.reset_window_to_default()

        yt_url = self.yt_url_field.text()

        if not self.is_url_valid(yt_url):
            self.display_error_message("URL is invalid")
            return 0

        try:
            # If the URL is valid and the video exist:
            self.count_button.setEnabled(False)  # Disable the count_button
            self.start_loading_animation()
            self.change_count_button_text(True)
            self.set_video_title(yt_url)
            self.set_video_thumbnail(yt_url)
            self.start_download_video_in_new_thread(yt_url)
        except Exception as ex:
            logging.warning(ex)
            self.display_error_message("Unknown problem encountered")

    def reset_window_to_default(self) -> None:
        """
        Clears the words table widget to remove any previous results.

        :param: None
        :return: None
        """
        self.words_table_widget.clear()
        self.words_table_widget.setRowCount(0)
        self.words_table_widget.setColumnCount(0)

    @staticmethod
    def is_url_valid(yt_url: str) -> bool:
        """
        Checks if the YouTube URL is valid and leads to video on YouTube.

        The function checks if it can create a YouTube object and retrieve the video stream from it, indicating
        that the URL is valid and leads to a video on YouTube.
        If the operation fails, it means that the URL is not valid or does not lead to a video on YouTube.

        :param yt_url: the YouTube video URL.
        :return: True if the URL is valid, False otherwise.
        """
        try:
            yt = YouTube(yt_url).streams.first().url
            return True
        except Exception as ex:
            logging.warning(ex)
            return False

    def set_video_title(self, yt_url: str) -> None:
        """
        Retrieves the title of the video and sets it.

        :param yt_url: the YouTube video URL.
        :return: None
        """
        yt = YouTube(yt_url)
        title = yt.title
        self.yt_title_widget.setStyleSheet("color: rgb(0, 0, 0);")
        self.yt_title_widget.setText(f"Title:  {title}")

    def set_video_thumbnail(self, yt_url: str) -> None:
        """
        Retrieves the title of the video and sets it.

        :param yt_url: the YouTube video URL.
        :return: None
        """
        try:
            # Get video ID from URL (YouTube URL can be in two different versions: with "channel" and without it)
            if "channel" in yt_url:
                yt_id = yt_url[yt_url.index("v") + 2: yt_url.index("&")]
            else:
                yt_id = yt_url[yt_url.index("=") + 1:]
            # Download thumbnail and set it to widget
            thumbnail = urllib.request.urlretrieve(f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg")
            pixmap = QPixmap(thumbnail[0])
            pixmap = pixmap.scaled(120, 50)
            self.icon_widget.setPixmap(pixmap)
            # Remove created temporary file with thumbnail
            os.remove(thumbnail[0])
        except Exception as ex:
            logging.warning(ex)

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

    def start_download_video_in_new_thread(self, yt_url: str) -> None:
        """
        Starts a new thread for downloading the video from the given YouTube URL.

        The remaining part of the code is executed in the connected method handle_finished_downloading_video() after
        completing all the operations in the new thread.

        :param yt_url: the YouTube video URL.
        :return: None
        """
        self.download_video_thread = modules.download_video_thread.DownloadVideoThread(yt_url)
        self.download_video_thread.finished.connect(self.handle_finished_downloading_video)
        self.download_video_thread.start()

    def handle_finished_downloading_video(self, file_path: str) -> None:
        """
        Handles the finished event of the DownloadVideoThread, which emits the file_path to the MP3 temporary file.
        Next starts counting words in this file.

        :param file_path: the path to the audio file
        :return: None
        """
        self.file_path = file_path  # this is necessary for later removal of the temporary file
        api_key = self.api_key_field.text()
        self.start_words_counting_in_new_thread(api_key, file_path)

    def start_words_counting_in_new_thread(self, api_key: str, file_path: str) -> None:
        """
        Starts a new thread for counting the words in the given file (temporary file with audio of YouTube video).

        The remaining part of the code is executed in the connected method handle_finished_counting_words() after
        completing all the operations in the new thread.

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
        with the counted words list and displays it on the screen. Finally, removes the temporary file containing
        the audio, stops the loading animation and changes the text in the count_button to "Count".

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
        # Remove downloaded file
        self.change_count_button_text(False)
        self.count_button.setEnabled(True)  # Re-enable the count_button
        self.stop_loading_animation()
        os.remove(self.file_path)

    def set_table_and_display_counted_words(self, counted_words_list: list) -> None:
        """
        Sets a table widget (by using set_table method) and displays the counted and sorted words with their counts.

        :param counted_words_list: list of tuples, each tuple contains a word and its count in the form (word, count)
        :return: None
        """
        self.set_table(counted_words_list)
        for i, word in enumerate(counted_words_list):
            item = QtWidgets.QTableWidgetItem(word[0])
            self.words_table_widget.setItem(i, 0, item)
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
        if error_code == "URL is invalid":
            message = "URL is invalid"
        elif error_code == "invalid api key":
            message = "Invalid API key"
        elif error_code == "file transcription error":
            message = "File transcription problem encountered"
        else:
            message = "Unknown problem encountered"
        self.yt_title_widget.setStyleSheet("color: rgb(200, 0, 0);")
        self.yt_title_widget.setText("Title:  " + message)
        self.icon_widget.clear()
