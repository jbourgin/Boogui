from gui.progress_widget import ProgressWidget
from eyetracking.Recherche_visuelle import ExperimentException

class TrialData:
    def __init__(self, experiment, subject_id, trial):
        self.experiment = experiment
        self.trial = trial
        self.image = None
        self.video = None
        self.subject_id = subject_id

    def getImage(self):
        if self.image != None:
            return self.image
        else:
            self.image = self.experiment.scanpath(self.subject_id, self.trial)
            return self.image

    def getVideo(self, parent):
        if self.video != None:
            return self.video
        else:
            progress = ProgressWidget(parent, 1)
            self.video = self.experiment.scanpathVideo(self.subject_id, self.trial, progress)
            progress.close()
            return self.video

class SubjectData:
    def __init__(self, experiment, input_file: str, progress = None):
        self.trial_datas = []
        self.experiment = experiment
        self.subject = self.experiment.processSubject(input_file, progress)

        for trial in self.subject.trials:
            self.trial_datas.append(TrialData(self.experiment, self.subject.id, trial))
