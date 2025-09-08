import logging

import requests

log = logging.getLogger(__name__)


class TranscribeMP3:
    """
    Transcribe audio files in MP3 format using the AssemblyAI API.
    """

    def __init__(self, file_path: str, api_key: str) -> None:
        """
        Initialize with audio file path and API key.

        :param file_path: Path to the audio file.
        :param api_key: API key for AssemblyAI.
        :return: None
        """
        self.file_path = file_path
        self.api_key = api_key
        log.debug("TranscribeMP3 initialized with file_path=%s", file_path)

    def on_execute(self) -> str:
        """
        Execute the transcription process.

        :param: None
        :return:
            - str, transcription text if successful.
            - str, "file transcription error" if transcription fails.
            - str, "invalid api key" if API key is invalid.
        """
        # Validate API key before making any requests
        if not self.check_api_key():
            log.warning("Invalid API key provided")
            return "invalid api key"

        try:
            # Step 1: Upload the file and get a temporary URL for AssemblyAI
            log.info("Uploading file to AssemblyAI: %s", self.file_path)
            upload_url = self.get_upload_url(self.file_path)["upload_url"]
            log.debug("Received upload URL")

            # Step 2: Submit the uploaded file for transcription, get transcription ID
            log.info("Submitting file for transcription")
            id_key = self.submit_processing(upload_url)["id"]
            log.debug("Received transcription ID: %s", id_key)

            # Step 3: Poll AssemblyAI until transcription is complete or fails
            while True:
                response = self.get_transcription(id_key)
                status = response.get("status")
                log.debug("Polling transcription status: %s", status)

                # If AssemblyAI explicitly reports an error -> stop and return error
                if status == "error":
                    log.error("Transcription failed with error response")
                    return "file transcription error"

                # If transcription is finished -> return the transcribed text
                if status not in ["processing", "queue"]:
                    log.info("Transcription completed successfully")
                    return response.get("text", "")

        except Exception as ex:
            # Any unexpected exception (network, JSON error, etc.) is logged
            log.error("Unexpected exception during transcription: %s", ex)
            return "file transcription error"

    def check_api_key(self) -> bool:
        """
        Check if the provided API key is valid.

        :param: None
        :return: True if the key is valid, False otherwise.
        """
        # Test endpoint for transcript creation
        endpoint = "https://api.assemblyai.com/v2/transcript"

        # Authorization header with provided API key
        headers = {
            "Authorization": "Token " + self.api_key
        }

        # Send a simple GET request to check authentication
        response = requests.get(endpoint, headers=headers)
        log.debug("API key validation status code: %s", response.status_code)

        # AssemblyAI returns 401 -> invalid key
        if response.status_code == 401:
            return False
        # Any other status -> assume key is valid
        else:
            return True

    @staticmethod
    def read_file(file_path: str, chunk_size=5242880) -> bytes:
        """
        Read a file in chunks and yield data.

        :param file_path: Path to the audio file.
        :param chunk_size: Chunk size in bytes.
        :return: File data chunks.
        """
        log.debug("Reading file in chunks: %s", file_path)
        # Open the audio file in binary mode
        with open(file_path, "rb") as file:
            while True:
                # Read file in chunks (default 5 MB)
                data = file.read(chunk_size)

                # If end of file reached -> stop loop
                if not data:
                    break

                # Yield the current chunk to the caller
                yield data

    def get_upload_url(self, file_path: str) -> dict:
        """
        Request upload URL for the audio file.

        :param file_path: Path to the audio file.
        :return: API response containing upload URL.
        """
        log.debug("Requesting upload URL for file: %s", file_path)
        # Authorization header with API key
        headers = {"authorization": self.api_key}

        # Upload the audio file in streaming chunks to AssemblyAI
        response = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers=headers,
            data=self.read_file(file_path),  # generator yields file chunks
        )
        log.debug("Upload request status: %s", response.status_code)

        # Return the parsed JSON response with the upload URL
        return response.json()

    def submit_processing(self, url: str) -> dict:
        """
        Submit the audio file for transcription.

        :param url: Upload URL for the audio file.
        :return: API response containing transcription ID.
        """
        log.debug("Submitting audio URL for processing")
        # Endpoint for submitting audio for transcription
        endpoint = "https://api.assemblyai.com/v2/transcript"

        # Request payload -> provide audio URL and enable extra features
        json = {
            "audio_url": url,
            "content_safety": True,
            "language_detection": True
        }

        # Headers for authorization and JSON body
        headers = {
            "authorization": self.api_key,
            "content-type": "application/json",
        }

        # Send request to start transcription
        response = requests.post(endpoint, json=json, headers=headers)
        log.debug("Submit processing status: %s", response.status_code)

        # Return parsed JSON response with transcription ID
        return response.json()

    def get_transcription(self, transcription_id: str) -> dict:
        """
        Get the current transcription result.

        :param transcription_id: Transcription job ID.
        :return: API response with status and text.
        """
        log.debug("Getting transcription status for ID=%s", transcription_id)
        # Build the endpoint URL using the transcription ID
        endpoint = f"https://api.assemblyai.com/v2/transcript/{transcription_id}"

        # Authorization header with API key
        headers = {
            "authorization": self.api_key,
        }

        # Request the current status and results of the transcription
        response = requests.get(endpoint, headers=headers)
        log.debug("Get transcription status code: %s", response.status_code)

        # Return parsed JSON response (contains status, text, errors, etc.)
        return response.json()
