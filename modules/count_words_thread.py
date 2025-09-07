from PyQt5.QtCore import QThread, pyqtSignal

import modules.count_words


class CountWordsThread(QThread):
    """
    Thread class for counting words in an audio file.
    """

    finished = pyqtSignal(object)  # A signal emitted when the thread has finished

    def __init__(self, file_path: str, api_key: str) -> None:
        """
        Initialize the CountWordsThread object.

        :param api_key: API key for AssemblyAI.
        :param file_path: Path to the audio file.
        :return: None
        """
        super().__init__()
        self.file_path = file_path
        self.api_key = api_key

    def run(self) -> None:
        """
        Run the thread: count words in the .mp3 file using CountWords,
        then emit the finished signal with results or error message.

        :param: None
        :return: None
        """
        # count words using the count_words module
        counted_words_list = modules.count_words.CountWords(self.file_path, self.api_key).count_words()
        # send the result via signal (word list or error message)
        self.finished.emit(counted_words_list)  # type: ignore[attr-defined]  # Qt signal, resolved at runtime
