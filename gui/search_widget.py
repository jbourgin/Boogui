from PyQt5.QtWidgets import QWidget, QProgressBar, QVBoxLayout, QLabel, QLineEdit
from PyQt5.QtWidgets import QApplication

class SearchWidget(QWidget):

    def __init__(self, parent):
        super().__init__(parent)

        self.textlogger = parent.logOutput

        # Widget dimensions
        self.height = 75
        self.width = 400

        #self.setAutoFillBackground(True)
        self.layout = QVBoxLayout()
        self.editline = QLineEdit()

        self.layout.addWidget(self.editline)
        self.setLayout(self.layout)

        x = self.textlogger.x() + self.textlogger.width() - self.width
        y = self.textlogger.y()
        print(x,y)
        self.setGeometry(x, y, self.width, self.height)
        self.editline.setText("Search")
        self.editline.selectAll()
        #self.setFixedHeight(self.height)
        #self.setFixedWidth(self.width)

        self.editline.returnPressed.connect(self.search)

        self.show()
        self.editline.setFocus()

    def get_text(self):
        return self.editline.text()

    def search(self):
        found = self.textlogger.find(self.get_text())
        if not found:
            cursor = self.textlogger.textCursor()
            cursor.setPosition(0)
            self.textlogger.setTextCursor(cursor)
            self.textlogger.find(self.get_text())
