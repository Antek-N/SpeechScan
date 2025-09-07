from pathlib import Path
from tempfile import TemporaryDirectory

from PyQt5.QtCore import QThread, pyqtSignal
from yt_dlp import YoutubeDL


class DownloadVideoThread(QThread):
    """Downloads audio from YouTube into a temporary directory (yt-dlp)."""
    finished = pyqtSignal(object)   # A signal emitted when the thread has finished
    failed = pyqtSignal(str)        # A signal emitted when the download fails (returns an error message)

    def __init__(self, yt_url: str) -> None:
        super().__init__()
        self.yt_url = yt_url
        self._tmpdir = None  # keep a reference to the temporary directory so it is not deleted too early

    def run(self) -> None:
        try:
            # download audio and return the file path
            file_path = self._download_audio()
            # emit finished signal with the full file path
            self.finished.emit(file_path)  # type: ignore[attr-defined]  # Qt signal, resolved at runtime
        except Exception as ex:
            # in case of error, emit failed signal with the error message
            self.failed.emit(str(ex))  # type: ignore[attr-defined]  # Qt signal, resolved at runtime

    def _download_audio(self) -> str:
        # create a temporary directory where the audio will be saved
        self._tmpdir = TemporaryDirectory()
        out_dir = Path(self._tmpdir.name)
        # set the output filename template
        out_tmpl = str(out_dir / "audio.%(ext)s")

        # yt-dlp configuration options
        yt_download_options = {
            "format": "bestaudio/best",  # choose the best available audio quality
            "outtmpl": out_tmpl,        # output filename template
            "quiet": True,              # suppress console logs
            "no_warnings": True,        # skip warnings
        }

        # download audio with yt-dlp
        with YoutubeDL(yt_download_options) as youtube_downloader:
            # download and get metadata
            info = youtube_downloader.extract_info(self.yt_url, download=True)
            # prepare the actual filename (with extension)
            file_path = youtube_downloader.prepare_filename(info)
        return file_path
