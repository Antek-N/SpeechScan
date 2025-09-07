import string
from collections import Counter
from typing import Union

import modules.transcribe_audio


class CountWords:
    """
    CountWords is a class that transcribes audio from a given audio file (using transcribe_audio.py)
    and counts the number of occurrences of each word in that transcription.
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

    def count_words(self) -> Union[list, str]:
        """
        Counts the number of occurrences of each word in a given audio file.
        (main method of the class)

        :return:
        - list of tuples, each tuple contains a word and its count in the form (word, count).
        - str, "file transcription error" - if there is an error in the transcription process.
        - str, "invalid api key" - if the AssemblyAI API key is invalid.
        """
        # 1. Get the transcription of the audio file (text)
        transcription_text = self.get_transcription()

        # 2. If transcription failed or the API key is invalid, return an error message
        if transcription_text in ["file transcription error", "invalid api key"]:
            return transcription_text
        else:
            # 3. Process the text: remove punctuation, convert to lowercase, split into a list of words
            words_list = self.process_text_to_list(transcription_text)

            # 4. Count words and sort them by the number of occurrences (descending order)
            counted_words_list = self.count_and_sort_words(words_list)

            # 5. Return the result as a list of tuples (word, count)
            return counted_words_list

    def get_transcription(self) -> str:
        """
        Transcribes audio from a file into text.

        :return: transcription of the audio
        """
        # Get transcription using the transcribe_audio module
        transcription_text = modules.transcribe_audio.TranscribeMP3(self.file_path, self.api_key).on_execute()
        return transcription_text

    @staticmethod
    def process_text_to_list(transcription_text: str) -> list:
        """
        Processes the given text by removing punctuation, converting all words to lowercase
        and splitting it into a list.

        :param transcription_text: text to process
        :return: list of str, processed words
        """
        # Convert all characters to lowercase
        transcription_text = transcription_text.lower()

        # Remove all punctuation
        transcription_text = transcription_text.translate(str.maketrans("", "", string.punctuation))

        # Split text into a list of words by spaces
        words_list = transcription_text.split()

        # Return the list of words
        return words_list

    @staticmethod
    def count_and_sort_words(words_list: list) -> list:
        """
        Count elements in the list and sort them by occurrences in descending order.

        :param words_list: list of str, words to count and sort
        :return: list of tuples, each tuple contains a word and its count in the form (word, count)
        """
        # Count the number of occurrences of each word in the list
        counted_words = Counter(words_list)

        # Sort words by the number of occurrences (descending order)
        counted_words = sorted(counted_words.items(), key=lambda x: x[1], reverse=True)

        # Return the list of tuples in the format (word, occurrence_count)
        return counted_words
