import logging
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from pytube import YouTube


class CheckURLThread(QThread):
    """
    CheckURLThread is a thread class for checking the validity of a given YouTube URL.
    It checks if the URL leads to a video on YouTube.
    """
    finished = pyqtSignal(object)  # A signal emitted when the thread has finished

    def __init__(self, yt_url: str) -> None:
        """
        Initializes the CheckURLThread object.

        :param yt_url: the YouTube video URL
        :return: None
        """
        super().__init__()
        self.yt_url = yt_url

    def run(self) -> None:
        """
        Runs the thread which checks the validity of the YouTube URL and emits the finished signal with
        the URL validation result.
        This method overrides the run method in the QThread class.

        :param: None
        :return: None
        """
        is_url_valid = self.is_url_valid()
        self.finished.emit(is_url_valid)

    def is_url_valid(self) -> bool:
        """
        Checks if the YouTube URL is valid and leads to video on YouTube.

        The function checks if it can create a YouTube object and retrieve the video stream from it, indicating
        that the URL is valid and leads to a video on YouTube.
        If the operation fails, it means that the URL is not valid or does not lead to a video on YouTube.

        :param: None
        :return: True if the URL is valid, False otherwise.
        """
        try:
            request = requests.get(self.yt_url)
            yt = YouTube(self.yt_url).streams.first().url
            return True
        except Exception as ex:
            logging.warning(ex)
            return False
