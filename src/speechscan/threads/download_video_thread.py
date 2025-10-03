import logging
from pathlib import Path
from tempfile import TemporaryDirectory

from PyQt5.QtCore import QThread, pyqtSignal
from yt_dlp import YoutubeDL

log = logging.getLogger(__name__)


class DownloadVideoThread(QThread):
    """
    Download audio from YouTube into a temporary directory (yt-dlp).
    """

    finished = pyqtSignal(object)  # A signal emitted when the thread has finished
    failed = pyqtSignal(str)  # A signal emitted when the download fails (returns an error message)
    _tmpdir: TemporaryDirectory[str] | None

    def __init__(self, yt_url: str) -> None:
        """
        Initialize the download thread.

        :param yt_url: YouTube video URL.
        :return: None
        """
        super().__init__()
        self.yt_url = yt_url
        self._tmpdir = None  # keep a reference to the temporary directory, so it is not deleted too early
        log.debug("DownloadVideoThread initialized with URL: %s", yt_url)

    def run(self) -> None:
        """
        Run the thread: download audio and emit finished or failed signal.

        :return: None
        """
        log.info("Starting download thread for URL: %s", self.yt_url)
        try:
            # download audio and return the file path
            file_path = self._download_audio()
            log.info("Download successful: %s", file_path)
            # emit finished signal with the full file path
            self.finished.emit(file_path)  # type: ignore[attr-defined]  # Qt signal, resolved at runtime
        except Exception as ex:
            log.error("Download failed for URL=%s | %s", self.yt_url, ex)
            # in case of error, emit failed signal with the error message
            self.failed.emit(str(ex))  # type: ignore[attr-defined]  # Qt signal, resolved at runtime

    def _download_audio(self) -> str:
        """
        Download audio using yt-dlp into a temporary directory.

        :return: Full path to the downloaded audio file.
        """
        log.debug("Creating temporary directory for download")
        # create a temporary directory where the audio will be saved
        self._tmpdir = TemporaryDirectory()
        tmpdir = self._tmpdir
        assert tmpdir is not None
        out_dir = Path(tmpdir.name)
        # set the output filename template
        out_tmpl = str(out_dir / "audio.%(ext)s")

        # yt-dlp configuration options
        yt_download_options = {
            "format": "bestaudio/best",  # choose the best available audio quality
            "outtmpl": out_tmpl,  # output filename template
            "quiet": True,  # suppress console logs
            "no_warnings": True,  # skip warnings
        }
        log.debug("yt-dlp options prepared: %s", yt_download_options)

        # download audio with yt-dlp
        with YoutubeDL(yt_download_options) as youtube_downloader:
            log.info("Downloading audio from YouTube...")
            # download and get metadata
            info = youtube_downloader.extract_info(self.yt_url, download=True)
            log.debug("Metadata retrieved: title=%s", info.get("title"))
            # prepare the actual filename (with the extension)
            file_path = youtube_downloader.prepare_filename(info)

        log.debug("Final downloaded file path: %s", file_path)
        return file_path
