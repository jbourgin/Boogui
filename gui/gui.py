import sys
import time
from PyQt5.QtWidgets import QMainWindow, QAction, QActionGroup, qApp, QWidget
from PyQt5.QtWidgets import QFileDialog, QTextEdit, QScrollArea, QErrorMessage
from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from eyetracking.smi import *
from eyetracking.Recherche_visuelle import *
from gui.utils import *
from gui.subject import *
from gui.progress_widget import ProgressWidget
from gui.video_widget import VideoWidget

import re #To format data lists

class Main(QMainWindow):

    scrollLayouWidth = 125
    previsuAreaWidth = 700

    def __init__(self):
        super().__init__()

        self.subject_datas = []

        self.subject_buttons = []

        # The main window widget
        self.main_wid = None

        self.initUI()

        # Window full screen
        #self.showFullScreen()
        self.showMaximized()

        quit = QAction("Quit", self)
        quit.triggered.connect(self.close)

    ###########################
    ######### UI INIT #########
    ###########################

    def initUI(self):
        self.setGeometry(300, 300, 600, 600)
        self.setWindowTitle('Eyetracking analysis')
        #self.setWindowIcon(QIcon('web.png'))

        self.set_menu()
        self.set_main_widget()
        self.show()

    def getTrialData(self, n_subject, n_trial):
        return self.subject_datas[n_subject].trial_datas[n_trial]

    def set_subject_scroller(self):
        # scroll area widget contents - layout
        self.subjecttrialScrollLayout = QVBoxLayout()
        self.subjecttrialScrollLayout.setAlignment(Qt.AlignTop)

        # scroll area widget contents
        self.subjectScrollWidget = QWidget()
        self.subjectScrollWidget.setLayout(self.subjecttrialScrollLayout)

        # scroll area
        self.subjectScrollArea = QScrollArea()
        self.subjectScrollArea.setWidgetResizable(True)
        self.subjectScrollArea.setWidget(self.subjectScrollWidget)
        self.subjectScrollArea.setFixedWidth(self.scrollLayouWidth)

        self.mainLayout.addWidget(self.subjectScrollArea)

    def set_trial_scroller(self):
        # scroll area widget contents - layout
        self.trialScrollLayout = QVBoxLayout()
        self.trialScrollLayout.setAlignment(Qt.AlignTop)

        # scroll area widget contents
        self.scrollWidget = QWidget()
        self.scrollWidget.setLayout(self.trialScrollLayout)

        # scroll area
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setFixedWidth(self.scrollLayouWidth)

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
        self.video_widget = VideoWidget(self)

        previsualizer_layout.addWidget(self.previsu_image)
        previsualizer_layout.addWidget(self.video_widget)
        self.previsualizer.setFixedWidth(self.previsuAreaWidth)

        self.mainLayout.addWidget(self.previsualizer)

    def set_main_widget(self):

        # main layout
        self.mainLayout = QHBoxLayout()

        self.set_subject_scroller()
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

        # Export menu item
        self.exportAct = QAction("&Export subjects", self)
        self.exportAct.setShortcut('Ctrl+S')
        self.exportAct.setStatusTip('Export files')
        self.exportAct.setEnabled(False)
        self.exportAct.triggered.connect(self.exportSubjects)

        # Setting menu bar
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAct)
        fileMenu.addAction(browseAct)
        fileMenu.addAction(self.exportAct)

        # Experiment menu
        ag = QActionGroup(self, exclusive=True)
        self.experiment_menu = menubar.addMenu('&Experiment')
        # Recherche visuelle
        setRechercheVisuelle = QAction('&Recherche visuelle', self, checkable = True)
        setRechercheVisuelle.triggered.connect(self.setRechercheVisuelle)
        a = ag.addAction(setRechercheVisuelle)
        self.experiment_menu.addAction(a)

        #Default experiment
        setRechercheVisuelle.setChecked(True)
        self.setRechercheVisuelle()

    # Called when the application stops
    # Clears the temporary folder
    def closeEvent(self, close_event):
        print('Closing application')
        clearTmpFolder()

    def clear_layouts(self):
        self.previsu_image.clear()
        self.video_widget.clear()
        self.logOutput.clear()

    ###########################
    ####### Experiments #######
    ###########################
    def getExperiment(self):
        return self.make_experiment

    def setRechercheVisuelle(self):
        def set():
            return Recherche_visuelle()
        self.make_experiment = set

    ###########################
    ###### I/O functions ######
    ###########################
    def file_open(self):
        filedialog = QFileDialog()
        filedialog.setDirectory('data')
        #filedialog.setOption(QFileDialog.Option.DontUseNativeDialog,False)
        filenames,_ = filedialog.getOpenFileNames(self, 'Open File')

        if len(filenames) > 0:
            # Enabling Save menu action
            self.exportAct.setEnabled(True)
            # Disabling change of experiment
            self.experiment_menu.setEnabled(False)

            progress = ProgressWidget(self, 2)
            progress.setText(0, 'Loading Subjects')
            progress.setMaximum(0, len(filenames))
            for filename in filenames:
                print('Reading subject file %s' % filename)
                selected_experiment = self.getExperiment()

                try:
                    self.subject_datas.append(SubjectData(selected_experiment(), filename, progress))

                    # Adding subject button
                    n_subject = len(self.subject_datas) - 1
                    button = QPushButton('Subject %i' % self.subject_datas[-1].subject.id)
                    self.subject_buttons.append(button)
                    button.setCheckable(True)
                    self.subjecttrialScrollLayout.addWidget(button)
                    button.clicked.connect(self.make_choose_subject(n_subject))
                    progress.increment(0)

                except ExperimentException as e:
                    error_dialog = QErrorMessage(self)
                    error_dialog.showMessage('File %s could not be read: %s' % (filename, str(e)))

            #closing message box
            progress.close()

    def exportSubjects(self):
        """
        hyp: len(subject_datas) > 0
        """
        createResultsFolder()
        filedialog = QFileDialog()
        filedialog.setDirectory(getResultsFolder())
        filename,_ = filedialog.getSaveFileName(self, 'Save File')
        # Creation of results file
        if len(filename) > 0:
            # Progress bar
            progress = ProgressWidget(self, 2)
            progress.setText(0, 'Exporting Subjects')
            progress.setMaximum(0, len(self.subject_datas))

            Recherche_visuelle.makeResultFile(filename)
            for subjectData in self.subject_datas:
                progress.increment(0)
                progress.setText(1, 'Exporting Trials')
                progress.setMaximum(1, len(subjectData.subject.trials))
                for trial in subjectData.subject.trials:
                    progress.increment(1)
                    subjectData.experiment.processTrial(subjectData.subject, trial, filename = filename)

            # Closing progress bar
            progress.close()

    ###########################
    ######## CALLBACKS ########
    ###########################
    def make_compute_video(self, n_subject, n_trial):
        def compute_video():
            print('computing video')
            vid_path = self.getTrialData(n_subject, n_trial).getVideo(self)
            self.video_widget.setVideo(vid_path)

        return compute_video

    def make_choose_subject(self, n_subject):
        def choose_subject():

            for i in range(len(self.subject_datas)):
                if i != n_subject:
                    self.subject_buttons[i].setChecked(False)

            self.setup_trials(n_subject)

        return choose_subject

    # Setups the Trial scroller components after selecting a subject
    def setup_trials(self, n_subject):
        print("setup trial")

        # Clearing layouts
        self.clear_layouts()
        clearLayout(self.trialScrollLayout)

        i = 0
        subject_data = self.subject_datas[n_subject]
        self.trial_buttons = []

        subject = subject_data.subject
        len_trials = len(subject.trials)
        for trial in subject.trials:
            button = QPushButton('Trial %i' % i, self)
            button.setCheckable(True)
            self.trial_buttons.append(button)
            self.trialScrollLayout.addWidget(button)
            button.clicked.connect(self.make_choose_trial(n_subject, i, trial))
            i += 1

    def make_choose_trial(self, n_subject, n_trial, trial):
        def choose_trial():
            print('choosing trial')
            self.clear_layouts()
            subject_data = self.subject_datas[n_subject]
            for i in range(len(self.trial_buttons)):
                if i != n_trial:
                    self.trial_buttons[i].setChecked(False)

            for entry in trial.entries:
                self.logOutput.append(str(entry))
            sb = self.logOutput.verticalScrollBar()
            sb.setValue(sb.minimum())

            image_name = joinPaths(getTmpFolder(), self.getTrialData(n_subject, n_trial).getImage())
            pixmap = QPixmap(image_name)
            self.previsu_image.setPixmap(pixmap)
            self.previsu_image.adjustSize()
            self.previsu_image.show()

            vid_name = self.getTrialData(n_subject, n_trial).video

            if vid_name is None:
                self.video_widget.setButton(self.make_compute_video(n_subject, n_trial))
            else:
                self.video_widget.setVideo(self.getTrialData(n_subject, n_trial).getVideo(self))

            self.video_widget.show()
        return choose_trial
