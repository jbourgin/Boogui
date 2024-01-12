from gui.progress_widget import ProgressWidget
from eyetracking.experiment import ExperimentException

class TrialData:
    def __init__(self, experiment, subject, trial):
        self.experiment = experiment
        self.trial = trial
        self.image = None
        self.video = None
        self.subject = subject

    def getImage(self):
        if self.image != None:
            return self.image
        else:
            self.image = self.experiment.plot(self.subject, self.trial)
            return self.image

    def getVideo(self, parent):
        if self.video != None:
            return self.video
        else:
            progress = ProgressWidget(parent, 1)
            self.video = self.experiment.scanpathVideo(self.subject, self.trial, progress)
            progress.close()
            return self.video

    def clearPlots(self):
        self.video = None
        self.image = None

class SubjectData:
    def __init__(self, experiment, input_file: str, progress = None):
        self.training_trial_datas = []
        self.trial_datas = []
        self.experiment = experiment
        self.subject = self.experiment.processSubject(input_file, progress)

        for trial in self.subject.training_trials:
            self.training_trial_datas.append(TrialData(self.experiment, self.subject, trial))

        for trial in self.subject.trials:
            self.trial_datas.append(TrialData(self.experiment, self.subject, trial))

    def getNTrainings(self):
        return len(self.training_trial_datas)
