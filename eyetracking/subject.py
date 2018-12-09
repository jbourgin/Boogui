from eyetracking.trial import *
from PyQt5.QtWidgets import QApplication

class Subject:

    def __init__(self, experiment, lines, id : int, group : str, progress = None):
        # list of training trials
        self.training_trials = []
        # list of trials
        self.trials = []
        # subject number
        self.id = id
        # subject group
        self.group = group

        if progress != None:
            progress.setText(1, 'Loading Trials: parsing entries')
            progress.setMaximum(1, experiment.n_trials)
            progress.setValue(1, 0)
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
                    if progress != None:
                        progress.setValue(1, n_trials)
                        # To close the file dialog window:
                        QApplication.processEvents()

    def getTrial(self, trial_number : int):
        for trial in self.trials:
            if trial.getTrialId() == trial_number:
                return trial
        return None
