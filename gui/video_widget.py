import sys, time, os
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QSlider, QStyle, QMessageBox
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, Qt

from eyetracking.utils import *
from gui.utils import *

class VideoWidget(QWidget):

    def __init__(self, parent):
        super().__init__(parent)

        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.stateChanged.connect(self.mediaStateChanged)
        self.media_player.positionChanged.connect(self.positionChanged)
        self.media_player.durationChanged.connect(self.durationChanged)
        self.media_player.error.connect(self.handleError)

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
        url = joinPaths(getTmpFolder(), path)
        self.clear()
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play)
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        play_vlc = QPushButton("Play with VLC")
        def f():
            self.playWithVLC(url)
        play_vlc.clicked.connect(f)
        play_vlc.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.setPosition)

        vid_wid = QVideoWidget()

        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(url)))
        self.media_player.setVideoOutput(vid_wid)

        self.layout.addWidget(vid_wid)
        self.layout.addWidget(self.position_slider)
        self.layout.addWidget(self.play_button)
        self.layout.addWidget(play_vlc)

    def play(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def playWithVLC(self, url):
        os.system('vlc %s' % url)

    def mediaStateChanged(self, state):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.play_button.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.play_button.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPlay))

    def positionChanged(self, position):
        self.position_slider.setValue(position)

    def durationChanged(self, duration):
        self.position_slider.setRange(0, duration)

    def setPosition(self, position):
        self.media_player.setPosition(position)

    def handleError(self):
        self.play_button.setEnabled(False)
        error_dialog = QMessageBox()
        error_dialog.warning(self, 'Error', 'Media player could not be loaded')
