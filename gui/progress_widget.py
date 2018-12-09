from PyQt5.QtWidgets import QWidget, QProgressBar, QVBoxLayout, QLabel

class ProgressException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class ProgressWidget(QWidget):

    def __init__(self, parent, n_bars):
        """
        @param n_bars number of progress bar
        """
        super().__init__(parent)

        # Widget dimensions
        self.height = 75
        self.width = 400

        self.setAutoFillBackground(True)
        self.layout = QVBoxLayout()

        self.progress_bars = []
        self.labels = []
        for i in range(n_bars):
            self.progress_bars.append(QProgressBar())
            self.labels.append(QLabel())

            self.layout.addWidget(self.labels[-1])
            self.layout.addWidget(self.progress_bars[-1])

        self.setFixedHeight(self.height * n_bars)
        self.setFixedWidth(self.width)

        self.setLayout(self.layout)

        center = parent.rect().center()
        self.move(center.x() - self.width/2, center.y() - self.height * n_bars/2)
        self.show()

        for i in range(n_bars):
            self.labels[i].setText('Loading')
            self.progress_bars[i].setValue(0)

    def setText(self, i, text):
        if i < 0 or i > len(self.labels):
            raise ProgressException('setText: incorrect index %i', i)
        self.labels[i].setText(text)

    def setMaximum(self, i, max):
        if i < 0 or i > len(self.progress_bars):
            raise ProgressException('setMaximum: incorrect index %i', i)
        self.progress_bars[i].setMaximum(max)

    def setValue(self, i, value):
        if i < 0 or i > len(self.progress_bars):
            raise ProgressException('setValue: incorrect index %i', i)
        self.progress_bars[i].setValue(value)
