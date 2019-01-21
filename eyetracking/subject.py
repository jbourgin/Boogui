from eyetracking.trial import *
from eyetracking.utils import *

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

        logTrace ('Parsing trials entries', Precision.TITLE)
        while lines != []:
            trial = Trial(experiment)
            lines = trial.setEntries(lines)
            if not trial.isEmpty():
                if trial.isTraining():
                    self.training_trials.append(trial)
                else:
                    self.trials.append(trial)
                    if progress != None:
                        progress.increment(1)

    def getTrial(self, trial_number : int):
        for trial in self.trials:
            if trial.getTrialId() == trial_number:
                return trial
        return None
