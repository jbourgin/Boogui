import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, QActionGroup, qApp, QWidget
from PyQt5.QtWidgets import QFileDialog, QProgressBar
from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtGui import QIcon

from smi import *
from Recherche_visuelle import *
import re #To format data lists

class Main(QMainWindow):

    # The current experiment
    experiment = Recherche_visuelle()

    # The current eyetracker
    eyetracker = None

    # The current opened subject
    subject = None

    # The main window widget
    main_wid = None

    def __init__(self):
        super().__init__()

        self.initUI()


    def initUI(self):

        self.setGeometry(300, 300, 300, 220)
        #self.setWindowTitle('Icon')
        #self.setWindowIcon(QIcon('web.png'))

        self.set_menu()

        self.set_main_widget()

        self.show()

    def set_main_widget(self):
        self.wid = QWidget(self)
        self.setCentralWidget(self.wid)

        hbox = QHBoxLayout()
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addLayout(hbox)

        self.wid.setLayout(vbox)

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
        self.eyetracker = Eyelink(self.experiment)

    def setSMI(self):
        print('Setting SMI')
        self.eyetracker = Smi(self.experiment)

    def file_open(self):
        filename,_ = QFileDialog.getOpenFileName(self, 'Open File')
        print('Reading subject file %s' % filename)

        self.wid.progress = QProgressBar(self.wid)
        self.wid.progress.setGeometry(200, 80, 250, 20)
        self.wid.update()

        if self.eyetracker.isParsable(filename):
            datafile = open(filename,"r")

            with datafile:
                data = datafile.read()
                data = list(data.splitlines())

                #We add a tabulation and space separator.
                data = [re.split("[\t ]+",line) for line in data]

                subject = Subject(self.eyetracker, data)
                self.setup_trial(filename)
        else:
            print('File not parsable by this eyetracker')

    # Setups the window components after opening a subject file
    def setup_trial(self, filename):
        print("setup trial")

        lbl = QLabel('Subject %s' % filename, self.wid)


if __name__ == '__main__':

    app = QApplication(sys.argv)

    mainWindow = Main()
    sys.exit(app.exec_())
