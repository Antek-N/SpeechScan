import sys
import os
import logging
import requests
import urllib.request
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.uic import loadUi
from PyQt5.QtGui import QPixmap
from pytube import YouTube


class TranscribeMP3:

    def __init__(self, file_path):
        self.file_path = file_path
        with open("api_key.txt", "r") as f:
            self.api_key = f.readline()  # Read api_key from api_key.txt file

    @staticmethod
    def read_file(file_path, chunk_size=5242880):
        with open(file_path, "rb") as file:
            while True:
                data = file.read(chunk_size)
                if not data:
                    break
                yield data

    def get_upload_url(self, file_path) -> dict:
        headers = {"authorization": self.api_key}
        response = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers=headers,
            data=self.read_file(file_path),
        )
        return response.json()

    def submit_processing(self, url) -> dict:
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
        endpoint = f"https://api.assemblyai.com/v2/transcript/{transcription_id}"
        headers = {
            "authorization": self.api_key,
        }
        response = requests.get(endpoint, headers=headers)
        return response.json()

    def on_execute(self):
        try:
            upload_url = self.get_upload_url(self.file_path)
            upload_url = upload_url["upload_url"]
            id_key = self.submit_processing(upload_url)
            id_key = id_key["id"]
            response = self.get_transcription(id_key)
            while response["status"] in ["processing", "queue"]:
                response = self.get_transcription(id_key)
                if response["status"] == "error":
                    print("error")
                    break
            return response["text"]
        except Exception as ex:
            logging.warning(ex)
            return 1


class StartWindow(QDialog):
    def __init__(self):
        super(StartWindow, self).__init__()
        loadUi("views/open_window.ui", self)
        self.file_button.clicked.connect(lambda: widgets.setCurrentIndex(1))  # Go to file_window
        self.youtube_button.clicked.connect(lambda: widgets.setCurrentIndex(2))  # Go to youtube_window


class FileWindow(QDialog):
    def __init__(self):
        super(FileWindow, self).__init__()
        loadUi("views/file_window.ui", self)
        self.cancel_button.clicked.connect(lambda: widgets.setCurrentIndex(0))  # Back to start_window


class YoutubeWindow(QDialog):
    def __init__(self):
        super(YoutubeWindow, self).__init__()
        loadUi("views/youtube_window.ui", self)
        self.submit_button.clicked.connect(self.submit)
        self.cancel_button.clicked.connect(lambda: widgets.setCurrentIndex(0))  # Back to start_window

    def submit(self):
        yt_url = self.yt_link_field.text()
        language = self.language_box.currentText()

        is_url_valid, request = self.check_if_url_valid(yt_url)
        if is_url_valid:
            is_video_exist = self.check_if_video_exist(request)
            if is_video_exist:
                self.set_video_title(yt_url)
                self.set_video_thumbnail(yt_url)
                video_path = self.download_video_as_mp3(yt_url)  # Download MP3 file from YT
                if video_path != 1:  # If video has been downloaded correctly
                    self.count(video_path)
                    os.remove(video_path)  # Remove downloaded file after all operations
            else:  # If video does not exist
                self.yt_title_field.setText("Title:  " + "Video does not exist")
                self.icon_field.clear()
        else:  # If URL is invalid
            self.yt_title_field.setText("Title:  " + "URL is invalid")
            self.icon_field.clear()

    @staticmethod
    def check_if_url_valid(yt_url):
        try:  # If URL is valid
            request = requests.get(yt_url)
            is_url_valid = 1
            return is_url_valid, request
        except Exception as ex:  # If URL is invalid
            logging.warning(ex)
            is_url_valid = 0
            return is_url_valid, 0

    @staticmethod
    def check_if_video_exist(request) -> bool:
        if "unavailable_video.png" in request.text or "www.youtube.com" not in request.text:  # If video does not exist
            is_video_exist = False
        else:  # If video exist
            is_video_exist = True
        return is_video_exist

    def set_video_title(self, yt_url):
        yt = YouTube(yt_url)
        title = yt.title
        self.yt_title_field.setText("Title:  " + title)

    def set_video_thumbnail(self, yt_url):
        try:
            if "channel" in yt_url:
                yt_id = yt_url[yt_url.index("v") + 2: yt_url.index("&")]  # Get video ID from URL
            else:  # yt URL can be in two different versions
                yt_id = yt_url[yt_url.index("=") + 1:]  # Get video ID from URL
            thumbnail = urllib.request.urlretrieve(f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg")
            pixmap = QPixmap(thumbnail[0])
            pixmap = pixmap.scaled(85, 45)
            self.icon_field.setPixmap(pixmap)
        except Exception as ex:
            logging.warning(ex)

    @staticmethod
    def download_video_as_mp3(yt_url):
        yt = YouTube(yt_url)
        video = yt.streams.filter(only_audio=True).first()
        video_path = video.download()
        try:
            # Convert video to MP3 file
            base, ext = os.path.splitext(video_path)
            new_video_path = base + '.mp3'
            os.rename(video_path, new_video_path)
            return new_video_path
        except Exception as ex:
            logging.warning(ex)
            try:
                os.remove(video_path)  # Delete MP4 file if it was created but not converted to MP3
            except Exception as ex:
                logging.warning(ex)
            return 1

    def count(self, video_path):
        text = self.mp3_to_text(video_path)
        print(text)

    @staticmethod
    def mp3_to_text(file_path):
        transcribe = TranscribeMP3(file_path)
        text = transcribe.on_execute()
        return text


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
