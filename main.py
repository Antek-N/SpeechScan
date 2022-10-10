import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog
from PyQt5.uic import loadUi
from PyQt5.QtGui import QPixmap
import urllib.request
from pytube import YouTube
import requests


class StartWindow(QDialog):
    def __init__(self):
        super(StartWindow, self).__init__()
        loadUi("views/open_window.ui", self)


class FileWindow(QDialog):
    def __init__(self):
        super(FileWindow, self).__init__()
        loadUi("views/file_window.ui", self)
        self.cancel_button.clicked.connect(lambda: widgets.setCurrentIndex(0))


class YoutubeWindow(QDialog):
    def __init__(self):
        super(YoutubeWindow, self).__init__()
        loadUi("views/youtube_window.ui", self)
        self.submit_button.clicked.connect(self.submit)
        self.cancel_button.clicked.connect(lambda: widgets.setCurrentIndex(0))  # Back to start window

    def submit(self):
        yt_url = self.yt_link_field.text()
        language = self.language_box.currentText()

        is_url_valid, request = self.check_url(yt_url)

        if is_url_valid:
            is_video_exist = self.check_if_video_exist(request)

            if is_video_exist:
                self.set_thumbnail(yt_url)
                self.set_title(yt_url)
                # self.count()

            else:  # If video does not exist
                self.yt_title_field.setText("Title:  " + "Video does not exist")
                self.icon_field.clear()

        else:  # If URL is invalid
            self.yt_title_field.setText("Title:  " + "URL is invalid")
            self.icon_field.clear()

    @staticmethod
    def check_if_video_exist(request):
        if "unavailable_video.png" in request.text or "www.youtube.com" not in request.text:  # If video does not exist
            is_video_exist = 0
        else:  # If video exist
            is_video_exist = 1
        return is_video_exist

    @staticmethod
    def check_url(yt_url):
        try:  # If URL is valid
            request = requests.get(yt_url)
            is_url_valid = 1
            return is_url_valid, request
        except:  # If URL is invalid
            is_url_valid = 0
            return is_url_valid, 0

    def set_title(self, yt_url):
        yt = YouTube(yt_url)
        title = yt.title
        self.yt_title_field.setText("Title:  " + title)

    def set_thumbnail(self, yt_url):
        yt_id = yt_url[yt_url.index("v") + 2:]
        thumbnail = urllib.request.urlretrieve("http://img.youtube.com/vi/" + yt_id + "/hqdefault.jpg")
        pixmap = QPixmap(thumbnail[0])
        pixmap = pixmap.scaled(85, 45)
        self.icon_field.setPixmap(pixmap)


app = QApplication(sys.argv)
start_window = StartWindow()
file_window = FileWindow()
youtube_window = YoutubeWindow()
widgets = QtWidgets.QStackedWidget()
widgets.addWidget(start_window)
widgets.addWidget(file_window)
widgets.addWidget(youtube_window)
start_window.file_button.clicked.connect(lambda: widgets.setCurrentIndex(1))
start_window.youtube_button.clicked.connect(lambda: widgets.setCurrentIndex(2))
widgets.resize(400, 325)
widgets.show()
sys.exit(app.exec_())
