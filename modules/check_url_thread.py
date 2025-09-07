import logging
from urllib.parse import urlparse, parse_qs

import requests
from PyQt5.QtCore import QThread, pyqtSignal


def extract_video_id(url: str):
    """
    Extracts the video ID from a YouTube URL.

    :param url: the YouTube video URL
    :return: the video ID if found, None otherwise
    """
    try:
        # Split the URL into components (scheme, netloc, path, query, etc.)
        parsed_url = urlparse(url.strip())

        # Extract the domain (e.g. 'youtu.be' or 'www.youtube.com'), convert to lowercase
        host = (parsed_url.netloc or "").lower()

        # Handle shortened links like: https://youtu.be/<video_id>
        if host.endswith("youtu.be"):
            # The video ID is in the URL path, e.g. "/dQw4w21WgXcQ"
            video_id = parsed_url.path.lstrip("/").split("/")[0]
            return video_id or None

        # Handle standard YouTube links
        if "youtube.com" in host:
            # 1. Standard format: https://www.youtube.com/watch?v=<video_id>
            if parsed_url.path == "/watch":
                # The 'v' parameter in the query string contains the video ID
                return parse_qs(parsed_url.query).get("v", [None])[0]

            # 2. Shorts format: https://www.youtube.com/shorts/<video_id>
            if parsed_url.path.startswith("/shorts/"):
                parts = parsed_url.path.split("/")
                return parts[2] if len(parts) > 2 else None

            # 3. Embed format: https://www.youtube.com/embed/<video_id>
            if parsed_url.path.startswith("/embed/"):
                parts = parsed_url.path.split("/")
                return parts[2] if len(parts) > 2 else None

        # If no format matches → no recognized ID
        return None

    # Handle potential exceptions (e.g. malformed URL)
    except (ValueError, IndexError, KeyError, AttributeError):
        return None


class CheckURLThread(QThread):
    """
    CheckURLThread is a thread class for checking the validity of a given YouTube URL.
    It checks if the URL leads to a video on YouTube using oEmbed (without pytube).
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
        Runs the thread which checks the validity of the YouTube URL and emits the finished signal
        with the URL validation result.
        This method overrides the run method in the QThread class.

        :param: None
        :return: None
        """
        self.finished.emit(self.is_url_valid())  # type: ignore[attr-defined]  # Qt signal, resolved at runtime

    def is_url_valid(self) -> bool:
        """
        Checks if a given YouTube URL is valid and points to an existing video.

        :param: None
        :return: True if the URL is valid, False otherwise
        """
        try:
            # Extract the video ID from the provided URL (e.g. "dQw4w21WgXcQ")
            video_id = extract_video_id(self.yt_url)

            # If no ID was found, the URL is invalid
            if not video_id:
                return False

            # Build the standard YouTube video link
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # Send an HTTP request to the YouTube oEmbed API
            # oEmbed returns video data (title, author, etc.) if the video exists
            response = requests.get(
                "https://www.youtube.com/oembed",
                params={"url": video_url, "format": "json"},
                timeout=10,  # safeguard: max 10s for a response
            )

            # If the response has status code 200 (OK), the video exists
            return response.status_code == 200

        except Exception as ex:
            # If an error occurred (e.g. no internet, timeout, invalid link)
            # log a warning and assume the URL is invalid
            logging.warning(ex)
            return False
