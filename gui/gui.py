import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, QActionGroup, qApp, QWidget
from PyQt5.QtWidgets import QFileDialog, QProgressBar, QTextEdit
from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtWidgets import QScrollArea, QFormLayout
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QUrl

from eyetracking.smi import *
from eyetracking.Recherche_visuelle import *
import re #To format data lists

class TrialData:
    def __init__(self, experiment, trial):
        self.experiment = experiment
        self.trial = trial
        self.image = None
        self.video = None

    def getImage(self):
        if self.image != None:
            return self.image
        else:
            self.image = self.experiment.scanpath(self.trial)
            return self.image

    def getVideo(self):
        if self.video != None:
            return self.video
        else:
            self.video = self.experiment.scanpathVideo(self.trial)
            return self.video

def clearLayout(layout):
  while layout.count():
    child = layout.takeAt(0)
    if child.widget():
      child.widget().deleteLater()

class Main(QMainWindow):

    def __init__(self):
        super().__init__()

        # The current experiment
        self.experiment = None

        # The current eyetracker
        self.eyetracker = None

        # The current opened subject
        self.subject = None

        self.trial_datas = []

        # The main window widget
        self.main_wid = None

        self.initUI()

        # Window full screen
        #self.showFullScreen()
        self.showMaximized()

    def initUI(self):

        self.setGeometry(300, 300, 600, 600)
        #self.setWindowTitle('Icon')
        #self.setWindowIcon(QIcon('web.png'))

        self.set_menu()

        self.set_main_widget()

        self.show()

    def set_video(self, n_trial):
        vid_wid = QVideoWidget()
        play_button = QPushButton("Play")
        play_button.clicked.connect(self.play)
        #url = 'http://localhost:8080/' +
        url = joinPaths(getTmpFolder(), self.trial_datas[n_trial].getVideo())
        print(url)
        self.mediaPlayer.setMedia(
            #QMediaContent(QUrl(url)))
            QMediaContent(QUrl.fromLocalFile(url)))
        self.mediaPlayer.setVideoOutput(vid_wid)
        self.previsu_vid_layout.addWidget(vid_wid)
        self.previsu_vid_layout.addWidget(play_button)

    def make_compute_video(self, n_trial):
        def compute_video():
            print('computing video')
            self.trial_datas[n_trial].getVideo()
            clearLayout(self.previsu_vid_layout)
            self.set_video(n_trial)

        return compute_video

    def play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def make_choose_trial(self, n_trial, trial):
        def choose_trial():
            print('choosing trial')
            self.logOutput.clear()

            for i in range(len(self.trial_buttons)):
                if i != n_trial:
                    self.trial_buttons[i].setChecked(False)

            for entry in trial.entries:
                self.logOutput.append(str(entry))
            sb = self.logOutput.verticalScrollBar()
            sb.setValue(sb.minimum())

            image_name = joinPaths(getTmpFolder(), self.trial_datas[n_trial].getImage())
            pixmap = QPixmap(image_name)
            self.previsu_image.setPixmap(pixmap)
            self.previsu_image.show()

            vid_name = self.trial_datas[n_trial].video
            clearLayout(self.previsu_vid_layout)
            if vid_name is None:
                button = QPushButton('Make video scanpath')
                button.clicked.connect(self.make_compute_video(n_trial))
                self.previsu_vid_layout.addWidget(button)
            else:
                self.set_video(n_trial)

            self.previsu_vid.show()
        return choose_trial

    def set_trial_scroller(self):
        # scroll area widget contents - layout
        self.scrollLayout = QVBoxLayout()

        # scroll area widget contents
        self.scrollWidget = QWidget()
        self.scrollWidget.setLayout(self.scrollLayout)

        # scroll area
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setFixedWidth(250)

        self.mainLayout.addWidget(self.scrollArea)

    def set_text_area(self):

        # text area
        self.logOutput = QTextEdit()
        self.logOutput.setReadOnly(True)
        self.logOutput.setLineWrapMode(QTextEdit.NoWrap)

        font = self.logOutput.font()
        font.setFamily("Courier")
        font.setPointSize(10)

        self.mainLayout.addWidget(self.logOutput)

    def set_previsualizer(self):
        self.previsualizer = QWidget()
        previsualizer_layout = QVBoxLayout()
        self.previsualizer.setLayout(previsualizer_layout)

        self.previsu_image = QLabel()
        self.previsu_vid = QWidget()

        self.previsu_vid_layout = QVBoxLayout()
        self.previsu_vid.setLayout(self.previsu_vid_layout)

        self.previsu_image.setFixedWidth(600)
        self.previsu_vid.setFixedWidth(600)

        self.previsu_image.setFixedHeight(400)
        self.previsu_vid.setFixedHeight(400)

        previsualizer_layout.addWidget(self.previsu_image)
        previsualizer_layout.addWidget(self.previsu_vid)

        self.mainLayout.addWidget(self.previsualizer)

    def set_main_widget(self):

        # main layout
        self.mainLayout = QHBoxLayout()

        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        self.set_trial_scroller()
        self.set_text_area()
        self.set_previsualizer()

        # central widget
        self.centralWidget = QWidget()
        self.centralWidget.setLayout(self.mainLayout)

        # set central widget
        self.setCentralWidget(self.centralWidget)

    def set_menu(self):
        # Quit menu item
        exitAct = QAction('&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(qApp.quit)

        # Browse menu item
        browseAct = QAction("&Open File", self)
        browseAct.setShortcut('Ctrl+O')
        browseAct.setStatusTip('Open file')
        browseAct.triggered.connect(self.file_open)

        # Setting menu bar
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAct)
        fileMenu.addAction(browseAct)

        # Eyetracker menu
        ag = QActionGroup(self, exclusive=True)
        eyeTrackerMenu = menubar.addMenu('&EyeTracker')
        # Eyelink
        setEyelinkAct = QAction("&Eyelink", self,  checkable=True)
        setEyelinkAct.setStatusTip('Eyelink')
        setEyelinkAct.triggered.connect(self.setEyelink)
        a = ag.addAction(setEyelinkAct)
        eyeTrackerMenu.addAction(a)
        # SMI
        setSMIAct = QAction("&SMI", self, checkable=True)
        setSMIAct.setStatusTip('SMI')
        setSMIAct.triggered.connect(self.setSMI)
        b = ag.addAction(setSMIAct)
        eyeTrackerMenu.addAction(b)

        # default eyetracker
        self.setEyelink()
        setEyelinkAct.setChecked(True)

    def setEyelink(self):
        print('Setting eyelink')
        print('TO UPDATE')
        self.eyetracker = Make_Eyelink()
        self.experiment = Recherche_visuelle(self.eyetracker)

    def setSMI(self):
        print('Setting SMI')
        print('TO UPDATE')
        self.eyetracker = Make_Smi()
        self.experiment = Recherche_visuelle(self.eyetracker)

    def file_open(self):
        filename,_ = QFileDialog.getOpenFileName(self, 'Open File')

        #self.wid.progress = QProgressBar(self.wid)
        #self.wid.progress.setGeometry(200, 80, 250, 20)
        #self.wid.update()

        progress_bar = QProgressBar(self)
        progress_bar.setGeometry(200, 80, 250, 20)
        progress_bar.show()

        if len(filename) > 0 and self.eyetracker.isParsable(filename):
            print('Reading subject file %s' % filename)
            subject = self.experiment.processSubject(filename, progress_bar)
            self.setup_trial(subject)
        else:
            print('File not parsable by this eyetracker')

        #closing progress bar
        progress_bar.hide()

    # Setups the window components after opening a subject file
    def setup_trial(self, subject):
        print("setup trial")

        progress_bar = QProgressBar(self)
        progress_bar.setGeometry(200, 80, 250, 20)
        progress_bar.show()
        i = 0
        self.trial_buttons = []
        self.trial_datas = []
        len_trials = len(subject.trials)
        for trial in subject.trials:
            button = QPushButton('Trial %i' % i, self)
            button.setCheckable(True)
            self.trial_datas.append(TrialData(self.experiment, trial))
            self.trial_buttons.append(button)
            self.scrollLayout.addWidget(button)
            button.clicked.connect(self.make_choose_trial(i, trial))
            progress_bar.setValue(i*100/len_trials)
            i += 1

        #closing progress bar
        progress_bar.hide()
        self.show()

if __name__ == '__main__':

    app = QApplication(sys.argv)

    mainWindow = Main()
    sys.exit(app.exec_())
