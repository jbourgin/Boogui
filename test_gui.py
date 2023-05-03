from PyQt5.QtWidgets import QApplication
from gui.gui import *
# https://pypi.org/project/pyqtdarktheme/
import qdarktheme


if __name__ == '__main__':

    app = QApplication(sys.argv)
    # Apply dark theme to app.
    qdarktheme.setup_theme()

    mainWindow = Main()
    sys.exit(app.exec_())
