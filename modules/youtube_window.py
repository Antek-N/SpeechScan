import logging
import os
import urllib.request
from typing import Union
from urllib.parse import parse_qs, urlparse

import requests
from PyQt5 import QtWidgets
from PyQt5.QtGui import QMovie, QPixmap
from PyQt5.QtWidgets import QAbstractItemView, QDialog, QHeaderView
from PyQt5.uic import loadUi  # type: ignore[import]

import modules.check_url_thread
import modules.count_words_thread
import modules.download_video_thread


def extract_video_id(url: str) -> Union[str, None]:
    """
    Extracts the video ID from a YouTube URL.

    :param url: the YouTube video URL
    :return: the video ID if found, None otherwise
    """
    try:
        # Parse the URL into components (scheme, host, path, query, etc.)
        parsed_url = urlparse(url.strip())
        host = (parsed_url.netloc or "").lower()

        # Case 1: Shortened URL format: youtu.be/<id>
        if host.endswith("youtu.be"):
            video_id = parsed_url.path.lstrip("/").split("/")[0]
            return video_id or None

        # Case 2: Standard YouTube domain
        if "youtube.com" in host:

            # Format: /watch?v=<id>
            if parsed_url.path == "/watch":
                return parse_qs(parsed_url.query).get("v", [None])[0]

            # Format: /shorts/<id>
            if parsed_url.path.startswith("/shorts/"):
                parts = parsed_url.path.split("/")
                return parts[2] if len(parts) > 2 else None

            # Format: /embed/<id>
            if parsed_url.path.startswith("/embed/"):
                parts = parsed_url.path.split("/")
                return parts[2] if len(parts) > 2 else None

        # No recognized format found
        return None
    except (ValueError, IndexError, KeyError, AttributeError):
        # In case of malformed URL or missing parts -> fail gracefully
        return None


class YouTubeWindow(QDialog):
    """
    YouTubeWindow is a class that loads GUI, downloads audio from YouTube,
    counts the words in it and displays it.

    YouTubeWindow class performs the following tasks:
    -loading YouTubeWindow GUI
    -checking the URL validity in a new thread
    -checking if the video exists
    -setting the video title and thumbnail
    -downloading the audio (yt-dlp)
    -sending audio file to count word occurrences in a new thread
    -displaying the results of count
    """
    # GUI element references (populated dynamically by loadUi)
    count_button: QtWidgets.QPushButton
    back_button: QtWidgets.QPushButton
    yt_url_field: QtWidgets.QLineEdit
    yt_title_widget: QtWidgets.QLabel
    icon_widget: QtWidgets.QLabel
    words_table_widget: QtWidgets.QTableWidget
    api_key_field: QtWidgets.QLineEdit
    loading_widget: QtWidgets.QLabel

    def __init__(self, widgets):
        """
        Initialize the YouTubeWindow and load user interface.

        :param widgets: stacked program widgets
        :return: None
        """
        super().__init__()
        # Load UI definition from Qt Designer .ui file
        loadUi("views/youtube_window.ui", self)

        # Connect "Count" button -> start submission process
        self.count_button.clicked.connect(self.submit)  # type: ignore[attr-defined]

        # Connect "Back" button -> return to start window (index 0 in stacked widgets)
        self.back_button.clicked.connect(lambda: widgets.setCurrentIndex(0))  # type: ignore[attr-defined]

        # Initialize attributes used later during video download and transcription
        self.temporary_file_path = ""  # will hold temporary audio file path
        self.yt_url = ""  # will hold YouTube URL entered by user
        self.download_video_thread = None  # thread for downloading audio
        self.count_thread = None  # thread for counting words
        self.check_url_thread = None  # thread for validating URL

    def submit(self) -> None:
        """
        Submits the process of counting the words in the video.

        Disables the count_button and changes the button text to "Counting...".
        Resets the window to the default by clearing the words table, title and thumbnail.
        Starts a new thread for checking the validity of the YouTube URL entered by the user
        and downloading the video.

        :param: None
        :return: None
        """
        # Disable the count button to prevent multiple clicks
        self.count_button.setEnabled(False)

        # Update button text -> "Counting..."
        self.change_count_button_text(True)

        # Show animated loading spinner
        self.start_loading_animation()

        # Reset title, thumbnail and table to default state
        self.reset_window_to_default()

        # Save the entered YouTube URL (trim whitespace)
        self.yt_url = self.yt_url_field.text().strip()

        # Launch background thread to validate the URL
        self.start_checking_url_in_new_thread()

    def reset_window_to_default(self) -> None:
        """
        Clears the words table, thumbnail and title widgets.

        :param: None
        :return: None
        """
        # Reset title label to default gray style and placeholder text
        self.yt_title_widget.setStyleSheet("color: rgb(177, 177, 177);")
        self.yt_title_widget.setText("Title:")

        # Clear video thumbnail
        self.icon_widget.clear()

        # Clear results table (remove headers, rows and data)
        self.words_table_widget.clear()
        self.words_table_widget.setRowCount(0)
        self.words_table_widget.setColumnCount(0)

    def start_checking_url_in_new_thread(self) -> None:
        """
        Starts a new thread for checking the validity of the YouTube URL entered by the user.

        The remaining part of the code is executed in the connected method
        handle_finished_url_checking() after completing all the operations in the new thread.

        :return: None
        """
        # Create background thread for URL validation
        self.check_url_thread = modules.check_url_thread.CheckURLThread(self.yt_url)

        # Connect thread's finished signal -> callback handler
        self.check_url_thread.finished.connect(self.handle_finished_url_checking)

        # Start the thread (runs asynchronously)
        self.check_url_thread.start()

    def handle_finished_url_checking(self, is_valid: bool) -> Union[None, int]:
        """
        Handles the finished event of the CheckURLThread, which checks if the given YouTube URL
        is valid and leads to a video.

        If the URL is valid and the video exists, sets the title and thumbnail of the video
        and starts downloading the video in a new thread.
        If the operation fails, it displays an error message.

        :param is_valid: True if the URL is valid, False otherwise
        :return: None if no error occurs, 0 otherwise
        """
        if is_valid:
            try:
                # Fetch and display video metadata (title and thumbnail)
                self.set_video_title(self.yt_url)
                self.set_video_thumbnail(self.yt_url)

                # Start background thread to download video audio
                self.start_download_video_in_new_thread(self.yt_url)
            except Exception as ex:
                # Log error and reset UI to safe state
                logging.warning(ex)
                self.display_error_message("Unknown problem encountered")
                self.stop_loading_animation()
                self.change_count_button_text(False)
                self.count_button.setEnabled(True)
        else:
            # Invalid URL -> show error and reset UI
            self.display_error_message("URL is invalid")
            self.stop_loading_animation()
            self.change_count_button_text(False)
            self.count_button.setEnabled(True)
            return 0

    def set_video_title(self, yt_url: str) -> None:
        """
        Retrieves the title of the video and sets it.

        :param yt_url: the YouTube video URL
        :return: None
        """
        # Extract video ID from the URL
        video_id = extract_video_id(yt_url)
        if not video_id:
            # If no ID could be extracted, show fallback title
            self.yt_title_widget.setText("Title:  (cannot read)")
            return

        # Build canonical watch URL
        film_url = f"https://www.youtube.com/watch?v={video_id}"
        try:
            # Query YouTube's oEmbed API for metadata
            response = requests.get(
                "https://www.youtube.com/oembed",
                params={"url": film_url, "format": "json"},
                timeout=10,
            )
            response.raise_for_status()

            # Extract title from JSON response
            title = response.json().get("title", "")
            self.yt_title_widget.setText(f"Title:  {title}")
        except Exception as ex:
            # On failure -> log warning and show fallback text
            logging.warning(ex)
            self.yt_title_widget.setText("Title:  (cannot read)")

    def set_video_thumbnail(self, yt_url: str) -> None:
        """
        Retrieves the thumbnail of the video and sets it.

        :param yt_url: the YouTube video URL
        :return: None
        """
        try:
            # Extract video ID from the URL
            video_id = extract_video_id(yt_url)
            if not video_id:
                return

            # Build thumbnail URL and download it temporarily
            thumb_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
            thumbnail = urllib.request.urlretrieve(thumb_url)

            # Load thumbnail into a pixmap and scale it
            pixmap = QPixmap(thumbnail[0]).scaled(120, 50)
            self.icon_widget.setPixmap(pixmap)

            # Remove temporary file from disk
            os.remove(thumbnail[0])
        except Exception as ex:
            # Log any failure (network, I/O, etc.)
            logging.warning(ex)

    def start_download_video_in_new_thread(self, yt_url: str) -> None:
        """
        Starts a new thread for downloading the video from the given YouTube URL.

        The remaining part of the code is executed in the connected method
        handle_finished_downloading_video() after completing all the operations in the new thread.

        :param yt_url: the YouTube video URL
        :return: None
        """
        # Extract video ID to confirm validity
        video_id = extract_video_id(yt_url)
        if not video_id:
            # Invalid -> show error and restore UI state
            self.display_error_message("URL is invalid")
            self.stop_loading_animation()
            self.change_count_button_text(False)
            self.count_button.setEnabled(True)
            return

        # Build canonical watch URL for yt-dlp
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        # Create worker thread for video download
        self.download_video_thread = modules.download_video_thread.DownloadVideoThread(video_url)

        # Connect thread signals -> success and failure handlers
        self.download_video_thread.finished.connect(self.handle_finished_downloading_video)
        self.download_video_thread.failed.connect(self.handle_download_failed)

        # Start the thread
        self.download_video_thread.start()

    def handle_finished_downloading_video(self, file_path: str) -> None:
        """
        Handles the finished event of the DownloadVideoThread, which emits the file_path to the audio file.
        Next starts counting words in this file.

        :param file_path: the path to the audio file
        :return: None
        """
        # Save path of the temporary audio file (for later cleanup)
        self.temporary_file_path = file_path

        # Get AssemblyAI API key from input field
        api_key = self.api_key_field.text()

        # Start worker thread to count words in the downloaded audio
        self.start_words_counting_in_new_thread(api_key, file_path)

    def handle_download_failed(self, message: str) -> None:
        """
        Handles the failed event of the DownloadVideoThread.

        :param message: error message
        :return: None
        """
        # Log the failure for debugging
        logging.warning(message)

        # Show error in UI and restore state
        self.display_error_message("Unknown problem encountered")
        self.stop_loading_animation()
        self.change_count_button_text(False)
        self.count_button.setEnabled(True)

    def start_words_counting_in_new_thread(self, api_key: str, file_path: str) -> None:
        """
        Starts a new thread for counting the words in the given file.

        The remaining part of the code is executed in the connected method
        handle_finished_counting_words() after completing all the operations in the new thread.

        :param api_key: the API key for AssemblyAI
        :param file_path: the path to the audio file
        :return: None
        """
        # Create worker thread for transcription + word counting
        self.count_thread = modules.count_words_thread.CountWordsThread(file_path, api_key)

        # Connect thread's finished signal -> callback handler
        self.count_thread.finished.connect(self.handle_finished_counting_words)

        # Start the thread asynchronously
        self.count_thread.start()

    def handle_finished_counting_words(self, counted_words_list: Union[list, str]) -> Union[None, int]:
        """
        Handles the finished event of the CountWordsThread, which emits the result of counting words in an audio file.
        If the result is an error message, displays it on the screen. Otherwise, sets up a table widget
        with the counted words list and displays it. Finally, removes the temporary file containing the audio,
        stops the loading animation and changes the text in the count_button to "Count".

        :param counted_words_list: list of tuples with (word, count) or str with error
        :return: None if no error occurs, 0 otherwise
        """
        if counted_words_list in ["invalid api key", "file transcription error"]:
            # Show error message to user
            self.display_error_message(counted_words_list)

            # Reset UI state
            self.stop_loading_animation()
            self.change_count_button_text(False)
            self.count_button.setEnabled(True)

            # Attempt to delete temporary audio file
            try:
                os.remove(self.temporary_file_path)
            except Exception as ex:
                logging.warning(ex)
            return 0
        else:
            # Display counted words in table
            self.set_table_and_display_counted_words(counted_words_list)

        # Restore button state
        self.change_count_button_text(False)
        self.count_button.setEnabled(True)

        # Stop loading animation
        self.stop_loading_animation()

        # Attempt to clean up temporary audio file
        try:
            os.remove(self.temporary_file_path)
        except Exception as ex:
            logging.warning(ex)

    def set_table_and_display_counted_words(self, counted_words_list: list) -> None:
        """
        Sets a table widget and displays the counted and sorted words with their counts.

        :param counted_words_list: list of tuples, each tuple contains a word and its count
        :return: None
        """
        # Prepare the table with correct dimensions and headers
        self.set_table(counted_words_list)

        # Fill table row by row with words and their occurrence counts
        for i, word in enumerate(counted_words_list):
            # Column 0 -> word
            item = QtWidgets.QTableWidgetItem(word[0])
            self.words_table_widget.setItem(i, 0, item)

            # Column 1 -> number of occurrences
            item = QtWidgets.QTableWidgetItem(str(word[1]))
            self.words_table_widget.setItem(i, 1, item)

    def set_table(self, counted_words_list: list) -> None:
        """
        Sets the number of columns and rows in the table, sets column headers, and makes the table elements uneditable.

        :param counted_words_list: list of tuples, each tuple contains a word and its count
        :return: None
        """
        # Set number of rows equal to number of words
        self.words_table_widget.setRowCount(len(counted_words_list))

        # Always 2 columns: word and count
        self.words_table_widget.setColumnCount(2)

        # Define headers for both columns
        self.words_table_widget.setHorizontalHeaderLabels(["Word", "Number of occurrences"])

        # Make columns auto-resize to fill available space
        self.words_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Make cells read-only
        self.words_table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def start_loading_animation(self) -> None:
        """
        Starts the loading animation when counting the words.

        :param: None
        :return: None
        """
        # Load and start animated GIF for "loading" indicator
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
        # Stop the GIF animation and clear the widget
        self.loading_widget.movie().stop()
        self.loading_widget.clear()

    def change_count_button_text(self, is_counting: bool) -> None:
        """
        Changes the text on the count_button depending on the current state of counting.

        :param is_counting: True if counting is in progress, False otherwise
        :return: None
        """
        # Toggle button text depending on state
        if is_counting:
            self.count_button.setText("Counting...")
        else:
            self.count_button.setText("Count")

    def display_error_message(self, error_code: str) -> None:
        """
        Displays an error message if an error occurs during transcription.

        :param error_code: error code indicating the type of error
        :return: None
        """
        # Map error codes -> human-readable messages
        if error_code == "URL is invalid":
            message = "URL is invalid"
        elif error_code == "invalid api key":
            message = "Invalid API key"
        elif error_code == "file transcription error":
            message = "File transcription problem encountered"
        else:
            message = "Unknown problem encountered"

        # Show message in red in title widget
        self.yt_title_widget.setStyleSheet("color: rgb(200, 0, 0);")
        self.yt_title_widget.setText("Title:  " + message)

        # Clear thumbnail
        self.icon_widget.clear()
