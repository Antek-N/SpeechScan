import logging
import string
from collections import Counter

from speechscan.services.transcription.transcribe_audio import TranscribeMP3

log = logging.getLogger(__name__)


class CountWords:
    """
    Transcribe audio and count word occurrences.
    """

    def __init__(self, file_path: str, api_key: str) -> None:
        """
        Initialize the class with the audio file path and API key.

        :param file_path: Path to the audio file.
        :param api_key: API key for AssemblyAI.
        :return: None
        """
        self.file_path = file_path
        self.api_key = api_key
        log.debug("CountWords initialized with file_path=%s", file_path)

    def count_words(self) -> list[tuple[str, int]] | str:
        """
        Count word occurrences in the given audio file.

        :return:
            - List of (word, count) tuples if transcription is successful.
            - Str "file transcription error" if transcription fails.
            - Str "invalid api key" if the AssemblyAI API key is invalid.
        """
        log.info("Starting word count for file: %s", self.file_path)

        # 1. Get the transcription of the audio file (text)
        transcription_text = self.get_transcription()
        log.debug(
            "Transcription result: %s",
            transcription_text[:50] + "..." if isinstance(transcription_text, str) else transcription_text,
        )

        # 2. If transcription failed or the API key is invalid, return an error message
        if transcription_text in ["file transcription error", "invalid api key"]:
            log.warning("Transcription failed with message: %s", transcription_text)
            return transcription_text
        else:
            # 3. Process the text: remove punctuation, convert to lowercase, split into a list of words
            words_list = self.process_text_to_list(transcription_text)
            log.debug("Processed text into word list with %d words", len(words_list))

            # 4. Count words and sort them by the number of occurrences (descending order)
            counted_words_list = self.count_and_sort_words(words_list)
            log.info("Counted %d unique words", len(counted_words_list))

            # 5. Return the result as a list of tuples (word, count)
            return counted_words_list

    def get_transcription(self) -> str:
        """
        Transcribe audio from a file into text.

        :return: Transcription text as str.
        """
        log.debug("Requesting transcription for file: %s", self.file_path)
        # Get transcription using the transcribe_audio module
        transcription_text = TranscribeMP3(self.file_path, self.api_key).on_execute()
        if transcription_text in ["file transcription error", "invalid api key"]:
            log.warning("Transcription error: %s", transcription_text)
        else:
            log.debug("Transcription succeeded, length=%d characters", len(transcription_text))
        return transcription_text

    @staticmethod
    def process_text_to_list(transcription_text: str) -> list[str]:
        """
        Process text: remove punctuation, lowercase, split into words.

        :param transcription_text: Text to process.
        :return: List of words.
        """
        log.debug("Processing transcription text into word list")
        # Convert all characters to lowercase
        transcription_text = transcription_text.lower()

        # Remove all punctuation
        transcription_text = transcription_text.translate(str.maketrans("", "", string.punctuation))

        # Split text into a list of words by spaces
        words_list = transcription_text.split()
        log.debug("Created word list with %d items", len(words_list))

        # Return the list of words
        return words_list

    @staticmethod
    def count_and_sort_words(words_list: list[str]) -> list[tuple[str, int]]:
        """
        Count elements in the list and sort them by frequency (descending).

        :param words_list: List of words to count and sort.
        :return: List of (word, count) tuples.
        """
        log.debug("Counting and sorting %d words", len(words_list))
        counted = Counter(words_list)
        sorted_words = sorted(counted.items(), key=lambda x: x[1], reverse=True)
        log.debug("Sorted word list with %d unique words", len(sorted_words))
        return sorted_words
