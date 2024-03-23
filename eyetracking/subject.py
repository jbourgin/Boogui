from eyetracking.trial import *
from eyetracking.utils import *

class Subject:
    def __init__(self, experiment, n_trials: int, lines, id : int, group : str, progress = None):
        # list of training trials
        self.training_trials = []
        # list of trials
        self.trials = []
        # subject number
        self.id = id
        # subject group
        self.group = group
        # record freq in Hz
        self.recordFreq = experiment.getRecordFreq(lines)

        if progress != None:
            progress.setText(1, 'Loading Trials: parsing entries')
            progress.setMaximum(1, n_trials)

        logTrace ('Parsing trials entries', Precision.TITLE)
        while lines != []:
            trial = Trial(experiment)
            lines = trial.setEntries(lines)
            try:
                logTrace ('Checking trial validity', Precision.NORMAL)
                trial.checkValid()
                # WARNING 20/03/24 : no longer exclude trials when no gaze data inside (to avoid skipping rows). We kept skipping rows on old experiments (Gaze, Engagement, Prosaccade, RPETE), inside processTrial
                # if not trial.isEmpty():
                if trial.isTraining():
                    self.training_trials.append(trial)
                else:
                    self.trials.append(trial)
                    if progress != None:
                        progress.increment(1)
            except Exception as error:
                print('%s skipped because of errors' % trial)
                print(error)
                continue


    def getTrial(self, trial_number : int):
        for trial in self.trials:
            if trial.id == trial_number:
                return trial
        return None
