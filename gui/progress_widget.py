from PyQt5.QtWidgets import QWidget, QProgressBar, QVBoxLayout, QLabel

class ProgressWidget(QWidget):

    # Widget dimensions
    height = 150
    width = 400

    def __init__(self, parent):
        super().__init__(parent)

        self.setAutoFillBackground(True)
        self.layout = QVBoxLayout()

        # Progress bars
        self.progress_bar_subject = QProgressBar()
        self.progress_bar_trial = QProgressBar()

        # Labels
        self.label_subject = QLabel()
        self.label_trial = QLabel()

        self.layout.addWidget(self.label_subject)
        self.layout.addWidget(self.progress_bar_subject)
        self.layout.addWidget(self.label_trial)
        self.layout.addWidget(self.progress_bar_trial)

        self.setFixedHeight(self.height)
        self.setFixedWidth(self.width)

        self.setLayout(self.layout)

        center = parent.rect().center()
        self.move(center.x() - self.width/2, center.y() - self.height/2)
        self.show()

        self.label_subject.setText('Loading Subjects')
        self.progress_bar_subject.setValue(0)
        self.label_trial.setText('Loading Trials')
        self.progress_bar_trial.setValue(0)
