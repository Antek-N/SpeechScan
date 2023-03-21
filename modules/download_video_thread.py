from tempfile import NamedTemporaryFile
from PyQt5.QtCore import QThread, pyqtSignal
from pytube import YouTube


class DownloadVideoThread(QThread):
    """DownloadVideoThread is a thread class for downloading video from given YouTube URL."""

    finished = pyqtSignal(object)  # A signal emitted when the thread has finished

    def __init__(self, yt_url: str) -> None:
        """
        Initializes the DownloadVideoThread object.

        :param yt_url: the YouTube video URL
        :return: None
        """
        super().__init__()
        self.yt_url = yt_url

    def run(self) -> None:
        """
        Runs the thread which downloading audio from the video from YouTube video to temporary .MP3 file.
        Emits the finished signal with the path to this downloaded temporary .MP3 file.
        This method overrides the run method in the QThread class.

        :param: None
        :return: None
        """
        file_path = self.download_video_as_mp3()
        self.finished.emit(file_path)

    def download_video_as_mp3(self) -> str:
        """
        Downloads video to temporary .MP3 file and returns path to this file

        :param: None
        :return: the path to the downloaded MP3 file.
        """
        yt = YouTube(self.yt_url)
        video = yt.streams.filter(only_audio=True).first()
        temp_file = NamedTemporaryFile(delete=False, suffix=".mp3")
        video.download(filename=temp_file.name)
        file_path = temp_file.name
        return file_path
