from eyetracking.trial import *
from PyQt5.QtWidgets import QApplication

class Subject:

    def __init__(self, experiment, lines, id : int, group : str, progress_bar = None):
        # list of training trials
        self.training_trials = []
        # list of trials
        self.trials = []
        # subject number
        self.id = id
        # subject group
        self.group = group

        if progress_bar != None:
            progress_bar.label_trial.setText('Loading Trials: parsing entries')
            progress_bar.progress_bar_trial.setMaximum(experiment.n_trials)
            progress_bar.progress_bar_trial.setValue(0)
        n_trials = 0
        print('Parsing trials entries')
        while lines != []:
            trial = Trial(experiment)
            lines = trial.setEntries(lines)
            if not trial.isEmpty():
                if experiment.eyetracker.isTraining(trial):
                    self.training_trials.append(trial)
                else:
                    self.trials.append(trial)
                    n_trials += 1
                    if progress_bar != None:
                        progress_bar.progress_bar_trial.setValue(n_trials)
                        # To close the file dialog window:
                        QApplication.processEvents()

    def getTrial(self, trial_number : int):
        for trial in self.trials:
            if trial.getTrialId() == trial_number:
                return trial
        return None
