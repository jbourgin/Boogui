import sys
import time
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl

from eyetracking.utils import *
from gui.utils import *

class VideoWidget(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

    def clear(self):
        clearLayout(self.layout)

    def setButton(self, callback) -> None:
        self.clear()
        self.button = QPushButton('Make video scanpath')
        self.button.clicked.connect(callback)
        self.layout.addWidget(self.button)

    def setVideo(self, path: str) -> None:
        self.clear()
        vid_wid = QVideoWidget()
        play_button = QPushButton("Play")
        play_button.clicked.connect(self.play)
        url = joinPaths(getTmpFolder(), path)
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(url)))
        self.media_player.setVideoOutput(vid_wid)
        self.layout.addWidget(vid_wid)
        self.layout.addWidget(play_button)

    def play(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
