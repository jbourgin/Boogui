import sys, os, time
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QAction, QActionGroup, qApp, QWidget
from PyQt5.QtWidgets import QFileDialog, QTextEdit, QScrollArea, QMessageBox, QButtonGroup
from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QShortcut
from PyQt5.QtGui import QPixmap, QIcon, QKeySequence, QCloseEvent
from PyQt5.QtMultimedia import QSound
from PyQt5.QtCore import Qt, pyqtSlot

from eyetracking.smi import *
from eyetracking.Visual_search import *
from eyetracking.Gaze_contingent import *
from eyetracking.Visual_selection import *
from eyetracking.Prosaccade import *
from eyetracking.Antisaccade import *
from gui.utils import *
from gui.subject import *
from gui.progress_widget import ProgressWidget
from gui.search_widget import SearchWidget
from gui.video_widget import VideoWidget

import re #To format data lists
import traceback

class Main(QMainWindow):

    scrollLayouWidth = 125
    previsuAreaWidth = 700

    # folder where the "open" file dialog starts
    dataDirectory = 'data'

    def __init__(self):
        super().__init__()

        self.subject_datas = []

        self.subject_buttons = QButtonGroup()
        self.subject_buttons.setExclusive(True)

        # The main window widget
        self.main_wid = None
        self.frequency = 10

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
        icon = QIcon(get_ressources_file('icon.png'))
        self.setWindowIcon(icon)

        self.set_menu()
        self.set_main_widget()
        self.set_shortcuts()
        self.show()

    def set_shortcuts(self):
        self.search_line = None
        shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut.activated.connect(self.open_search)

    def getTrialData(self, n_subject, trial):
        if trial.isTraining():
            return next(
                t for t in self.subject_datas[n_subject].training_trial_datas if t.trial == trial)
        else:
            return next(t for t in self.subject_datas[n_subject].trial_datas if t.trial == trial)

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
        self.scrollArea.setFixedWidth(self.scrollLayouWidth + 25)

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
        exitAct.triggered.connect(self.close)

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

        # Export menu item
        self.clear = QAction("&Clear subjects", self)
        self.clear.setEnabled(False)
        self.clear.triggered.connect(self.clear_subjects)

        # Setting menu bar
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAct)
        fileMenu.addAction(browseAct)
        fileMenu.addAction(self.exportAct)
        fileMenu.addAction(self.clear)

        # Experiment menu
        ag = QActionGroup(self, exclusive=True)
        self.experiment_menu = menubar.addMenu('&Experiment')
        # Visual search
        setVisualSearch = QAction('&Visual search', self, checkable = True)
        setVisualSearch.triggered.connect(self.setVisualSearch)
        a = ag.addAction(setVisualSearch)
        self.experiment_menu.addAction(a)

        # GazeContingent
        setGazeContingent = QAction('&Gaze Contingent', self, checkable = True)
        setGazeContingent.triggered.connect(self.setGazeContingent)
        b = ag.addAction(setGazeContingent)
        self.experiment_menu.addAction(b)

        # Visual selection
        setVisualSelection = QAction('&Visual selection', self, checkable = True)
        setVisualSelection.triggered.connect(self.setVisualSelection)
        c = ag.addAction(setVisualSelection)
        self.experiment_menu.addAction(c)

        # Prosaccade
        setProsaccade = QAction('Prosaccade', self, checkable = True)
        setProsaccade.triggered.connect(self.setProsaccade)
        d = ag.addAction(setProsaccade)
        self.experiment_menu.addAction(d)

        # Antisaccade
        setAntisaccade = QAction('Antisaccade', self, checkable = True)
        setAntisaccade.triggered.connect(self.setAntisaccade)
        e = ag.addAction(setAntisaccade)
        self.experiment_menu.addAction(e)

        #Default experiment
        setVisualSearch.setChecked(True)
        self.setVisualSearch()

        # Config menu
        self.config_menu = menubar.addMenu('&Config')

        # Frequency submenu
        ag = QActionGroup(self, exclusive=True)
        frequency_menu = self.config_menu.addMenu('&Frequency')
        # Visual search
        for i in [1,2,5,10]:
            setFrequency = QAction('&%i' % i, self, checkable = True)
            setFrequency.triggered.connect(self.setFrequency(i))
            a = ag.addAction(setFrequency)
            frequency_menu.addAction(a)
        setFrequency.setChecked(True)

        # Warning submenu
        #warning_menu = self.config_menu.addMenu('&Exception is Warning')
        setWarning = self.config_menu.addAction('&Exception is Warning')
        setWarning.setCheckable(True)
        setWarning.setChecked(EntryList.ENTRYLISTEXCEPTION_WARNING)
        def f():
            EntryList.ENTRYLISTEXCEPTION_WARNING = not EntryList.ENTRYLISTEXCEPTION_WARNING
        setWarning.triggered.connect(f)

        # Recalibrate menu
        recalibrate = QAction('&Recalibrate all subjects', self)
        def f_recalibrate():
            for subjectData in self.subject_datas:
                g = self.recalibrate(subjectData)
                g()
        recalibrate.triggered.connect(f_recalibrate)
        self.config_menu.addAction(recalibrate)

    # Called when the application stops
    # Clears the temporary folder
    def closeEvent(self, close_event):
        logTrace ('Closing application', Precision.TITLE)
        clearTmpFolder()

    def clear_layouts(self):
        self.previsu_image.clear()
        self.video_widget.clear()
        self.logOutput.clear()

    def clear_subjects(self):
        self.subject_datas = []
        self.subject_buttons = QButtonGroup()
        self.subject_buttons.setExclusive(True)
        # Disabling Save menu action
        self.exportAct.setEnabled(False)
        # Enabling change of experiment
        self.experiment_menu.setEnabled(True)
        # Disbaling clear menu action
        self.clear.setEnabled(False)

        # Deleting subject buttons
        for i in reversed(range(self.subjecttrialScrollLayout.count())):
            self.subjecttrialScrollLayout.itemAt(i).widget().setParent(None)

        # Deleting trial buttons
        for i in reversed(range(self.trialScrollLayout.count())):
            self.trialScrollLayout.itemAt(i).widget().setParent(None)

        self.clear_layouts()

    def raiseWarning(self, e, error_message: str) -> None:
        sound = QSound(get_ressources_file('error.wav'))
        sound.play()
        error_dialog = QMessageBox()
        error_dialog.warning(self, 'Error', traceback.format_exc())

    ###########################
    ####### Experiments #######
    ###########################
    def getExperiment(self):
        return self.make_experiment

    def setVisualSearch(self):
        def set():
            return Visual_search()
        self.make_experiment = set

    def setGazeContingent(self):
        def set():
            return Gaze_contingent()
        self.make_experiment = set

    def setVisualSelection(self):
        def set():
            return Visual_selection()
        self.make_experiment = set

    def setProsaccade(self):
        def set():
            return Prosaccade()
        self.make_experiment = set

    def setAntisaccade(self):
        def set():
            return Antisaccade()
        self.make_experiment = set

    def setFrequency(self, frequency : int):
        def set():
            self.frequency = frequency
            for subject in self.subject_datas:
                subject.setFrequency(frequency)
        return set

    ###########################
    ###### I/O functions ######
    ###########################
    def file_open(self):

        filedialog = QFileDialog()
        filedialog.setDirectory(self.dataDirectory)
        filenames,_ = filedialog.getOpenFileNames(self, 'Open File')
        if len(filenames) > 0:
            # Storing new default data folder
            self.dataDirectory = '/'.join(filenames[0].split('/')[0:-1])
            # Enabling Save menu action
            self.exportAct.setEnabled(True)
            # Disabling change of experiment
            self.experiment_menu.setEnabled(False)
            # Enabling clear menu action
            self.clear.setEnabled(True)

            progress = ProgressWidget(self, 2)
            progress.setText(0, 'Loading Subjects')
            progress.setMaximum(0, len(filenames))
            for filename in filenames:
                logTrace ('Reading subject file %s' % filename, Precision.INPUT)
                selected_experiment = self.getExperiment()

                try:
                    subject = SubjectData(selected_experiment(), filename, self.frequency, progress)
                    self.subject_datas.append(subject)

                    # Adding subject button
                    n_subject = len(self.subject_datas) - 1
                    button = QPushButton('Subject %i' % self.subject_datas[-1].subject.id)
                    self.subject_buttons.addButton(button)
                    # set button context menu policy
                    button.setContextMenuPolicy(Qt.ActionsContextMenu)
                    # create context menu
                    #popMenu = QtWidgets.QMenu(self)
                    a = QAction('Recalibrate', self)
                    a.triggered.connect(self.recalibrate(subject))
                    button.addAction(a)
                    button.setCheckable(True)
                    self.subjecttrialScrollLayout.addWidget(button)
                    button.clicked.connect(self.make_choose_subject(n_subject))
                    progress.increment(0)

                except Exception as e:
                    self.raiseWarning(e, 'File %s could not be read:\n%s' % (filename, str(e)))

            #closing message box
            progress.close()

    def recalibrate(self, subject: Subject) -> None:
        def f():
            progress = ProgressWidget(self, 1)
            progress.setText(0, 'Recalibration')
            progress.setMaximum(0, 4)
            subject.experiment.recalibrate(subject.subject,
                (progress, 0)
            )
            subject.clearScanpaths()
            progress.close()
        return f

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
            try:
                # Progress bar
                progress = ProgressWidget(self, 2)
                progress.setText(0, 'Exporting Subjects')
                progress.setMaximum(0, len(self.subject_datas))

                selected_experiment = self.getExperiment()
                selected_experiment().makeResultFile(filename)
                for subjectData in self.subject_datas:
                    progress.increment(0)
                    progress.setText(1, 'Exporting Trials')
                    progress.setMaximum(1, len(subjectData.subject.trials))
                    for trial in subjectData.subject.trials:
                        progress.increment(1)
                        subjectData.experiment.processTrial(subjectData.subject, trial, filename = filename)
                selected_experiment().postProcess(filename)

            except Exception as e:
                self.raiseWarning(e, 'Error while exporting to file %s: \n%s' % (filename, str(e)))

            # Closing progress bar
            progress.close()

    ###########################
    ######## CALLBACKS ########
    ###########################
    def make_compute_video(self, n_subject, trial):
        def compute_video():
            logTrace ('computing video', Precision.NORMAL)
            vid_path = self.getTrialData(n_subject, trial).getVideo(self)
            self.video_widget.setVideo(vid_path)

        return compute_video

    def make_choose_subject(self, n_subject):
        def choose_subject():
            self.setup_trials(n_subject)
        return choose_subject

    # Setups the Trial scroller components after selecting a subject
    def setup_trials(self, n_subject):
        # Clearing layouts
        self.clear_layouts()
        clearLayout(self.trialScrollLayout)

        subject_data = self.subject_datas[n_subject]
        subject = subject_data.subject

        self.buttonGroup = QButtonGroup()
        self.buttonGroup.setExclusive(True)
        i = 0
        for trial in subject.training_trials:
            button = QPushButton('Training %i' % i, self)
            button.setCheckable(True)
            self.buttonGroup.addButton(button)
            self.trialScrollLayout.addWidget(button)
            button.clicked.connect(self.make_choose_trial(n_subject, i, trial))
            i += 1

        i = 0
        for trial in subject.trials:
            widget = QWidget()
            layout = QHBoxLayout()
            widget.setLayout(layout)

            button = QPushButton('Trial %i' % i, self)
            button.setCheckable(True)
            self.buttonGroup.addButton(button)
            button.clicked.connect(self.make_choose_trial(n_subject, i, trial))

            checkbox = QtWidgets.QCheckBox(self)
            checkbox.setChecked(trial.discarded)

            #checkbox.stateChanged.connect(lambda t=trial,box=checkbox: t.discard(box.isChecked()))
            checkbox.stateChanged.connect(self.discardTrial(trial, checkbox))
            layout.addWidget(button)
            layout.addWidget(checkbox)

            self.trialScrollLayout.addWidget(widget)

            i += 1

    def discardTrial(self, trial, box):
        def f():
            trial.discard(box.isChecked())
        return f

    def make_choose_trial(self, n_subject, n_trial, trial):
        def choose_trial():
            logTrace ('choosing trial', Precision.NORMAL)
            self.clear_layouts()

            for entry in trial.entries:
                self.logOutput.append(str(entry))
            sb = self.logOutput.verticalScrollBar()
            sb.setValue(sb.minimum())

            image_name = joinPaths(getTmpFolder(), self.getTrialData(n_subject, trial).getImage())
            pixmap = QPixmap(image_name)
            self.previsu_image.setPixmap(pixmap)
            self.previsu_image.adjustSize()
            self.previsu_image.show()

            vid_name = self.getTrialData(n_subject, trial).video

            if vid_name is None:
                self.video_widget.setButton(self.make_compute_video(n_subject, trial))
            else:
                self.video_widget.setVideo(self.getTrialData(n_subject, trial).getVideo(self))

            self.video_widget.show()
        return choose_trial

    @pyqtSlot()
    def open_search(self):
        if self.search_line is None:
            self.search_line = SearchWidget(self)
        else:
            self.search_line.close()
            self.search_line = None

    def closeEvent(self, event):
        messagebox = QMessageBox(QMessageBox.Question, "Are you sure you want to quit?",
        "Boo will miss you...",
        buttons = QMessageBox.Yes | QMessageBox.No,
        parent = self)
        messagebox.setDefaultButton(QMessageBox.No)
        messagebox.setIconPixmap(QPixmap(get_ressources_file("boo.png")))
        sound = QSound(get_ressources_file('squeak.wav'))
        sound.play()
        reply = messagebox.exec_()

        #reply = QMessageBox.question(self,
        #    'Are you sure you want to quit?',
        #    'Boo will miss you...',
        #    QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            super(Main, self).closeEvent(event)
        else:
            event.ignore()
