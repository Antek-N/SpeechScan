import logging

import requests


class TranscribeMP3:
    """TranscribeMP3 is a class to transcribe audio files in MP3 format.

    The class uses the AssemblyAI API to transcribe the audio file and return the transcribed text.
    The class can be initialized with the path to the audio file and the API key for AssemblyAI.
    The main method of the class, on_execute(), returns the transcription text if successful.
    If there is an error in the transcription process, it returns 1. If the API key check is invalid, it returns 2.
    """

    def __init__(self, file_path: str, api_key: str) -> None:
        """
        Initialize the class with the audio file path and API key.

        :param file_path: The path to the audio file
        :param api_key: the API key for AssemblyAI
        :return: None
        """
        self.file_path = file_path
        self.api_key = api_key

    def on_execute(self) -> str:
        """
        Main method of TranscribeMP3 class.

        :param: None
        :returns:
        -str, transcription text - If transcription is successful.
        -str, "file transcription error" - if there is an error in the transcription process.
        -str, "invalid api key" - if AssemblyAI API key is invalid.
        """
        # Validate API key before making any requests
        if not self.check_api_key():
            return "invalid api key"

        try:
            # Step 1: Upload the file and get a temporary URL for AssemblyAI
            upload_url = self.get_upload_url(self.file_path)["upload_url"]

            # Step 2: Submit the uploaded file for transcription, get transcription ID
            id_key = self.submit_processing(upload_url)["id"]

            # Step 3: Poll AssemblyAI until transcription is complete or fails
            while True:
                response = self.get_transcription(id_key)

                # If AssemblyAI explicitly reports an error -> stop and return error
                if response["status"] == "error":
                    return "file transcription error"

                # If transcription is finished -> return the transcribed text
                if response["status"] not in ["processing", "queue"]:
                    return response["text"]

        except Exception as ex:
            # Any unexpected exception (network, JSON error, etc.) is logged
            logging.warning(ex)
            return "file transcription error"

    def check_api_key(self) -> bool:
        """
        Check if the API key is valid.

        :param: None
        :return: True if the API key is valid, False otherwise
        """
        # Test endpoint for transcript creation
        endpoint = "https://api.assemblyai.com/v2/transcript"

        # Authorization header with provided API key
        headers = {
            "Authorization": "Token " + self.api_key
        }

        # Send a simple GET request to check authentication
        response = requests.get(endpoint, headers=headers)

        # AssemblyAI returns 401 -> invalid key
        if response.status_code == 401:
            return False
        # Any other status -> assume key is valid
        else:
            return True

    @staticmethod
    def read_file(file_path: str, chunk_size=5242880) -> bytes:
        """
        Read a file in chunks and yield the data.

        :param file_path: the path to the audio file
        :param chunk_size: the chunk size to read the file in
        :return: yields the data from audio file in chunks
        """
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
        Make a request to the AssemblyAI API to get the upload URL for the audio file.

        :param file_path: the path to the audio file
        :return: the response from the API containing the upload URL
        """
        # Authorization header with API key
        headers = {"authorization": self.api_key}

        # Upload the audio file in streaming chunks to AssemblyAI
        response = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers=headers,
            data=self.read_file(file_path),  # generator yields file chunks
        )

        # Return the parsed JSON response with the upload URL
        return response.json()

    def submit_processing(self, url: str) -> dict:
        """
        Make a request to the AssemblyAI API to submit the audio file for processing.

        :param url: the upload URL for the audio file
        :return: the response from the API containing the transcription ID
        """
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

        # Return parsed JSON response with transcription ID
        return response.json()

    def get_transcription(self, transcription_id: str) -> dict:
        """
        Get the transcription of the audio file.

        :param transcription_id: the ID of the transcription
        :return: the response from the API containing the transcribed text
        """
        # Build the endpoint URL using the transcription ID
        endpoint = f"https://api.assemblyai.com/v2/transcript/{transcription_id}"

        # Authorization header with API key
        headers = {
            "authorization": self.api_key,
        }

        # Request the current status and results of the transcription
        response = requests.get(endpoint, headers=headers)

        # Return parsed JSON response (contains status, text, errors, etc.)
        return response.json()
