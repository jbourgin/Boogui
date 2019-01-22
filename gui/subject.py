from gui.progress_widget import ProgressWidget
from eyetracking.Recherche_visuelle import ExperimentException

class TrialData:
    def __init__(self, experiment, subject_id, trial, frequency):
        self.experiment = experiment
        self.trial = trial
        self.image = None
        self.video = None
        self.subject_id = subject_id
        self.frequency = frequency

    def getImage(self):
        if self.image != None:
            return self.image
        else:
            self.image = self.experiment.scanpath(self.subject_id, self.trial, self.frequency)
            return self.image

    def getVideo(self, parent):
        if self.video != None:
            return self.video
        else:
            progress = ProgressWidget(parent, 1)
            self.video = self.experiment.scanpathVideo(self.subject_id, self.trial, self.frequency, progress)
            progress.close()
            return self.video

    def setFrequency(self, frequency : int):
        if self.frequency != frequency:
            self.image = None
            self.video = None
            self.frequency = frequency

class SubjectData:
    def __init__(self, experiment, input_file: str, frequency, progress = None):
        self.training_trial_datas = []
        self.trial_datas = []
        self.experiment = experiment
        self.subject = self.experiment.processSubject(input_file, progress)

        for trial in self.subject.training_trials:
            self.training_trial_datas.append(TrialData(self.experiment, self.subject.id, trial, frequency))

        for trial in self.subject.trials:
            self.trial_datas.append(TrialData(self.experiment, self.subject.id, trial, frequency))

    def setFrequency(self, frequency : int):
        for trial in self.training_trial_datas:
            trial.setFrequency(frequency)

        for trial in self.trial_datas:
            trial.setFrequency(frequency)

    def getNTrainings(self):
        return len(self.training_trial_datas)
