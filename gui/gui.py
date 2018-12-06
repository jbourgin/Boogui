import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, QActionGroup, qApp, QWidget
from PyQt5.QtWidgets import QFileDialog, QProgressBar, QTextEdit
from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtWidgets import QScrollArea, QFormLayout

from eyetracking.smi import *
from eyetracking.Recherche_visuelle import *
import re #To format data lists

class Main(QMainWindow):

    def __init__(self):
        super().__init__()

        # The current experiment
        self.experiment = None

        # The current eyetracker
        self.eyetracker = None

        # The current opened subject
        self.subject = None

        # The main window widget
        self.main_wid = None

        self.initUI()

    def initUI(self):

        self.setGeometry(300, 300, 600, 600)
        #self.setWindowTitle('Icon')
        #self.setWindowIcon(QIcon('web.png'))

        self.set_menu()

        self.set_main_widget()

        self.show()

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

        return choose_trial

    def set_main_widget(self):
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

        # main layout
        self.mainLayout = QHBoxLayout()

        # text area
        self.logOutput = QTextEdit()
        self.logOutput.setReadOnly(True)
        self.logOutput.setLineWrapMode(QTextEdit.NoWrap)

        font = self.logOutput.font()
        font.setFamily("Courier")
        font.setPointSize(10)

        # add all main to the main vLayout
        self.mainLayout.addWidget(self.scrollArea)
        self.mainLayout.addWidget(self.logOutput)

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
        self.eyetracker = Eyelink()
        self.experiment = Recherche_visuelle(self.eyetracker)

    def setSMI(self):
        print('Setting SMI')
        self.eyetracker = Smi()
        self.experiment = Recherche_visuelle(self.eyetracker)

    def file_open(self):
        filename,_ = QFileDialog.getOpenFileName(self, 'Open File')
        print('Reading subject file %s' % filename)

        #self.wid.progress = QProgressBar(self.wid)
        #self.wid.progress.setGeometry(200, 80, 250, 20)
        #self.wid.update()

        if self.eyetracker.isParsable(filename):
            datafile = open(filename,"r")

            with datafile:
                data = datafile.read()
                data = list(data.splitlines())

                #We add a tabulation and space separator.
                data = [re.split("[\t ]+",line) for line in data]

                subject = Subject(self.experiment, data, 28, "SAS")
                # TODO: Read this data from file!
                self.setup_trial(subject)
        else:
            print('File not parsable by this eyetracker')

    # Setups the window components after opening a subject file
    def setup_trial(self, subject):
        print("setup trial")

        i = 0
        self.trial_buttons = []
        for trial in subject.trials:
            button = QPushButton('Trial %i' % i, self)
            button.setCheckable(True)
            self.trial_buttons.append(button)
            self.scrollLayout.addWidget(button)
            button.clicked.connect(self.make_choose_trial(i, trial))
            i += 1

        self.show()

if __name__ == '__main__':

    app = QApplication(sys.argv)

    mainWindow = Main()
    sys.exit(app.exec_())
