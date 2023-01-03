import sys
import os
import logging
import requests
import string
import urllib.request
from collections import Counter
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.uic import loadUi
from PyQt5.QtGui import QPixmap
from pytube import YouTube


class TranscribeMP3:

    def __init__(self, file_path):
        self.file_path = file_path
        # Read API key from the api_key.txt file
        with open("api_key.txt", "r") as f:
            self.api_key = f.readline()

    @staticmethod
    def read_file(file_path, chunk_size=5242880):
        # Read a file in chunks and yields the data
        with open(file_path, "rb") as file:
            while True:
                data = file.read(chunk_size)
                if not data:
                    break
                yield data

    def get_upload_url(self, file_path) -> dict:
        # Make a request to the AssemblyAI API to get an upload URL
        headers = {"authorization": self.api_key}
        response = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers=headers,
            data=self.read_file(file_path),
        )
        return response.json()

    def submit_processing(self, url) -> dict:
        # Make a request to the AssemblyAI API to submit the file for processing
        endpoint = "https://api.assemblyai.com/v2/transcript"
        json = {
            "audio_url": url,
            "content_safety": True,
        }
        headers = {
            "authorization": self.api_key,
            "content-type": "application/json",
        }
        response = requests.post(endpoint, json=json, headers=headers)
        return response.json()

    def get_transcription(self, transcription_id) -> dict:
        # Make a request to the AssemblyAI API to get the transcription
        endpoint = f"https://api.assemblyai.com/v2/transcript/{transcription_id}"
        headers = {
            "authorization": self.api_key,
        }
        response = requests.get(endpoint, headers=headers)
        return response.json()

    def on_execute(self):
        # Main method of TranscribeMP3 class
        try:
            # Get the upload URL and submit the file for processing
            upload_url = self.get_upload_url(self.file_path)
            upload_url = upload_url["upload_url"]
            id_key = self.submit_processing(upload_url)
            id_key = id_key["id"]

            # Poll the API until the transcription is finished
            response = self.get_transcription(id_key)
            while response["status"] in ["processing", "queue"]:
                response = self.get_transcription(id_key)
                if response["status"] == "error":
                    print("error")
                    break
            # Return the transcribed text
            return response["text"]
        except Exception as ex:
            logging.warning(ex)
            return 1


class StartWindow(QDialog):
    def __init__(self):
        super(StartWindow, self).__init__()
        loadUi("views/open_window.ui", self)
        # Go to file_window
        self.file_button.clicked.connect(lambda: widgets.setCurrentIndex(1))
        # Go to youtube_window
        self.youtube_button.clicked.connect(lambda: widgets.setCurrentIndex(2))


class FileWindow(QDialog):
    def __init__(self):
        super(FileWindow, self).__init__()
        loadUi("views/file_window.ui", self)
        # Back to start_window
        self.cancel_button.clicked.connect(lambda: widgets.setCurrentIndex(0))


class YoutubeWindow(QDialog):
    def __init__(self):
        super(YoutubeWindow, self).__init__()
        loadUi("views/youtube_window.ui", self)
        self.submit_button.clicked.connect(self.submit)
        # Back to start_window
        self.cancel_button.clicked.connect(lambda: widgets.setCurrentIndex(0))

    def submit(self):
        # Get YT_url and video language from text fields
        yt_url = self.yt_link_field.text()
        language = self.language_box.currentText()

        is_url_valid, request = self.check_if_url_valid(yt_url)
        if is_url_valid:
            is_video_exist = self.check_if_video_exist(request)
            if is_video_exist:
                self.set_video_title(yt_url)
                self.set_video_thumbnail(yt_url)
                # Download MP3 file from YT
                video_path = self.download_video_as_mp3(yt_url)
                # If video has been downloaded correctly count words and remove downloaded file
                if video_path != 1:
                    self.count(video_path)
                    os.remove(video_path)
            # If video does not exist
            else:
                self.yt_title_field.setText("Title:  " + "Video does not exist")
                self.icon_field.clear()
        # If URL is invalid
        else:
            self.yt_title_field.setText("Title:  " + "URL is invalid")
            self.icon_field.clear()

    @staticmethod
    def check_if_url_valid(yt_url):
        # If URL is valid
        try:
            request = requests.get(yt_url)
            is_url_valid = 1
            return is_url_valid, request
        # If URL is invalid
        except Exception as ex:
            logging.warning(ex)
            is_url_valid = 0
            return is_url_valid, 0

    @staticmethod
    def check_if_video_exist(request) -> bool:
        # If video does not exist
        if "unavailable_video.png" in request.text or "www.youtube.com" not in request.text:
            return False
        # If video exist
        else:
            return True

    def set_video_title(self, yt_url):
        yt = YouTube(yt_url)
        title = yt.title
        self.yt_title_field.setText("Title:  " + title)

    def set_video_thumbnail(self, yt_url):
        try:
            # Get video ID from URL (yt URL can be in two different versions)
            if "channel" in yt_url:
                yt_id = yt_url[yt_url.index("v") + 2: yt_url.index("&")]
            else:
                yt_id = yt_url[yt_url.index("=") + 1:]
            # Download thumbnail and set it to widget
            thumbnail = urllib.request.urlretrieve(f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg")
            pixmap = QPixmap(thumbnail[0])
            pixmap = pixmap.scaled(85, 45)
            self.icon_field.setPixmap(pixmap)
        except Exception as ex:
            logging.warning(ex)

    @staticmethod
    def download_video_as_mp3(yt_url):
        # Download video
        yt = YouTube(yt_url)
        video = yt.streams.filter(only_audio=True).first()
        video_path = video.download()
        # Convert video to MP3 file:
        try:
            base, ext = os.path.splitext(video_path)
            new_video_path = base + '.mp3'
            os.rename(video_path, new_video_path)
            return new_video_path
        except Exception as ex:
            logging.warning(ex)
            # Delete MP4 file if it was created but not converted to MP3
            try:
                os.remove(video_path)
            except Exception as ex:
                logging.warning(ex)
            return 1

    def count(self, video_path):
        # Get transcription from mp3 file
        text = self.mp3_to_text(video_path)
        # Remove punctuation from text
        text = text.translate(str.maketrans("", "", string.punctuation))
        # Make list of words from text and lower all words in list
        words = text.split()
        words = [word.lower() for word in words]
        # Count elements in list, convert to dictionary and sort it
        word_counts = Counter(words)
        word_counts = dict(word_counts)
        word_counts = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        # Put words to the text widgets (9 to first and second widget and 6 to third)
        output_str = ""
        for i, word in enumerate(word_counts):
            output_str += f"{word[0]} - {word[1]}\n"
            if i == 8:
                self.words_field.setText(output_str)
                output_str = ""
            if i == 17:
                self.words_field_2.setText(output_str)
                output_str = ""
            if i == 23:
                self.words_field_3.setText(output_str)
                output_str = ""

    @staticmethod
    def mp3_to_text(file_path):
        # Get transcribed text
        transcribe = TranscribeMP3(file_path)
        text = transcribe.on_execute()
        return text


# START
app = QApplication(sys.argv)
start_window = StartWindow()
file_window = FileWindow()
youtube_window = YoutubeWindow()
widgets = QtWidgets.QStackedWidget()
widgets.addWidget(start_window)
widgets.addWidget(file_window)
widgets.addWidget(youtube_window)
widgets.resize(400, 325)
widgets.show()
sys.exit(app.exec_())
