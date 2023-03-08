from PyQt5.QtCore import QThread, pyqtSignal
import modules.count_words


class CountWordsThread(QThread):
    """CountWordsThread is a thread class for counting words in a file."""

    finished = pyqtSignal(object)  # A signal emitted when the thread has finished

    def __init__(self, file_path, api_key):
        """
        Initializes the CountWordsThread object.

        :param api_key: the API key for AssemblyAI
        :param file_path: the path to the audio file
        :return: None
        """
        super().__init__()
        self.file_path = file_path
        self.api_key = api_key

    def run(self):
        """
        Runs the thread which counts the words in the .mp3 file using the CountWords class from the
        count_words module, emits the finished signal with the counted words list or error message as
        an argument.

        :param: None
        :return: None
        """
        counted_words_list = modules.count_words.CountWords(self.file_path, self.api_key).count_words()
        self.finished.emit(counted_words_list)
