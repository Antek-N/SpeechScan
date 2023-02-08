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

        :param file_path: the path to the audio file
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
        # Check if the API key is valid
        if not self.check_api_key():
            return "invalid api key"

        try:
            # Get the upload URL and submit the processing
            upload_url = self.get_upload_url(self.file_path)["upload_url"]
            id_key = self.submit_processing(upload_url)["id"]

            # Continuously check the status of transcription
            while True:
                response = self.get_transcription(id_key)
                # If there is an error in the transcription process, return 1
                if response["status"] == "error":
                    return "file transcription error"
                # If the status is not "processing" or "queue", return the transcribed text
                if response["status"] not in ["processing", "queue"]:
                    return response["text"]
        except Exception as ex:
            # Log any exceptions and return error
            logging.warning(ex)
            return "file transcription error"

    def check_api_key(self) -> bool:
        """
        Check if the API key is valid.

        :param: None
        :return: True if the API key is valid, False otherwise
        """
        endpoint = "https://api.assemblyai.com/v2/transcript"
        headers = {
            "Authorization": "Token " + self.api_key
        }
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 401:
            return False
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
        with open(file_path, "rb") as file:
            while True:
                data = file.read(chunk_size)
                if not data:
                    break
                yield data

    def get_upload_url(self, file_path: str) -> dict:
        """
        Make a request to the AssemblyAI API to get the upload URL for the audio file.

        :param file_path: the path to the audio file
        :return: the response from the API containing the upload URL
        """
        headers = {"authorization": self.api_key}
        response = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers=headers,
            data=self.read_file(file_path),
        )
        return response.json()

    def submit_processing(self, url: str) -> dict:
        """
        Make a request to the AssemblyAI API to submit the audio file for processing.

        :param url: the upload URL for the audio file
        :return: the response from the API containing the transcription ID
        """
        endpoint = "https://api.assemblyai.com/v2/transcript"
        json = {
            "audio_url": url,
            "content_safety": True,
            "language_detection": True
        }
        headers = {
            "authorization": self.api_key,
            "content-type": "application/json",
        }
        response = requests.post(endpoint, json=json, headers=headers)
        return response.json()

    def get_transcription(self, transcription_id: str) -> dict:
        """
        Get the transcription of the audio file.

        :param transcription_id: the ID of the transcription
        :return: the response from the API containing the transcribed text
        """
        endpoint = f"https://api.assemblyai.com/v2/transcript/{transcription_id}"
        headers = {
            "authorization": self.api_key,
        }
        response = requests.get(endpoint, headers=headers)
        return response.json()
