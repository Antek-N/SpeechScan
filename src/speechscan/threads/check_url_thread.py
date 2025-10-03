import logging
from urllib.parse import parse_qs, urlparse

import requests
from PyQt5.QtCore import QThread, pyqtSignal

log = logging.getLogger(__name__)


def extract_video_id(url: str) -> str | None:
    """
    Extract the video ID from a YouTube URL in various formats.

    :param url: YouTube video URL (standard, shorts, embed, or shortened).
    :return: Video ID string if found, otherwise None.
    """
    try:
        # Split the URL into components (scheme, netloc, path, query, etc.)
        parsed_url = urlparse(url.strip())
        # Extract the domain (e.g. 'youtu.be' or 'www.youtube.com'), convert to lowercase
        host = (parsed_url.netloc or "").lower()
        log.debug("Parsed URL: host=%s, path=%s, query=%s", host, parsed_url.path, parsed_url.query)

        # Handle shortened links like: https://youtu.be/<video_id>
        if host.endswith("youtu.be"):
            # The video ID is in the URL path, e.g. "/dQw4w21WgXcQ"
            video_id_short: str | None = parsed_url.path.lstrip("/").split("/")[0]
            if video_id_short:
                log.info("Extracted video ID from shortened URL: %s", video_id_short)
            else:
                log.warning("No video ID found in shortened URL")
            return video_id_short or None

        # Handle standard YouTube links
        if "youtube.com" in host:
            # 1. Standard format: https://www.youtube.com/watch?v=<video_id>
            if parsed_url.path == "/watch":
                # The 'v' parameter in the query string contains the video ID
                video_id_watch: str | None = parse_qs(parsed_url.query).get("v", [None])[0]
                if video_id_watch:
                    log.info("Extracted video ID from watch URL: %s", video_id_watch)
                else:
                    log.warning("No video ID found in watch URL")
                return video_id_watch

            # 2. Shorts format: https://www.youtube.com/shorts/<video_id>
            if parsed_url.path.startswith("/shorts/"):
                parts = parsed_url.path.split("/")
                video_id_shorts: str | None = parts[2] if len(parts) > 2 else None
                if video_id_shorts:
                    log.info("Extracted video ID from shorts URL: %s", video_id_shorts)
                else:
                    log.warning("No video ID found in shorts URL")
                return video_id_shorts

            # 3. Embed format: https://www.youtube.com/embed/<video_id>
            if parsed_url.path.startswith("/embed/"):
                parts = parsed_url.path.split("/")
                video_id_embed: str | None = parts[2] if len(parts) > 2 else None
                if video_id_embed:
                    log.info("Extracted video ID from embed URL: %s", video_id_embed)
                else:
                    log.warning("No video ID found in embed URL")
                return video_id_embed

        # If no format matches - no recognized ID
        log.warning("Unrecognized YouTube URL format: %s", url)
        return None

    # Handle potential exceptions (e.g., malformed URL)
    except (ValueError, IndexError, KeyError, AttributeError) as e:
        log.error("Error extracting video ID from URL=%s | %s", url, e)
        return None


class CheckURLThread(QThread):
    """
    Worker thread that validates a YouTube URL using the oEmbed API.
    """

    finished = pyqtSignal(object)  # A signal emitted when the thread has finished

    def __init__(self, yt_url: str) -> None:
        """
        Initialize the validation thread.

        :param yt_url: YouTube video URL to validate.
        :return: None
        """
        super().__init__()
        self.yt_url = yt_url
        log.debug("CheckURLThread initialized with URL: %s", yt_url)

    def run(self) -> None:
        """
        Execute the URL validation and emit the result.

        :return: None
        """
        log.info("Starting validation for URL: %s", self.yt_url)
        self.finished.emit(self.is_url_valid())  # type: ignore[attr-defined] # Qt signal, resolved at runtime
        log.info("Finished validation for URL: %s", self.yt_url)

    def is_url_valid(self) -> bool:
        """
        Check whether the provided YouTube URL points to an existing video.

        :return: True if valid video found, otherwise False.
        """
        try:
            # Extract the video ID from the provided URL (e.g. "dQw4w21WgXcQ")
            video_id = extract_video_id(self.yt_url)
            log.debug("Extracted video_id=%s", video_id)

            # If no ID was found, the URL is invalid
            if not video_id:
                log.warning("No video ID extracted from URL: %s", self.yt_url)
                return False

            # Build the standard YouTube video link
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            log.debug("Built video URL: %s", video_url)

            # Send an HTTP request to the YouTube oEmbed API
            # oEmbed returns video data (title, author, etc.) if the video exists
            response = requests.get(
                "https://www.youtube.com/oembed",
                params={"url": video_url, "format": "json"},
                timeout=10,  # safeguard: max 10s for a response
            )
            log.debug("oEmbed response status: %s", response.status_code)

            # If the response has status code 200 (OK), the video exists
            if response.status_code == 200:
                log.info("Video exists: %s", video_url)
                return True
            else:
                log.warning("Video not found (status=%s) for URL: %s", response.status_code, video_url)
                return False

        except Exception as ex:
            # If an error occurred (e.g., no internet, timeout, invalid link)
            # log a warning and assume the URL is invalid
            log.error("Exception while validating URL=%s | %s", self.yt_url, ex)
            return False
