import attr
from abc import ABC, abstractmethod
from typing import List, Dict, Union

from eyetracking.utils import *
from eyetracking.subject import *

class ExperimentException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

class Experiment (ABC):

    def __init__(self):
        self.expected_features = set()
        self.eyetrackers = []

    @abstractmethod
    def processTrial(self, subject : Subject, trial : Trial) -> None:
        pass

    # Creates an image scanpath for one trial.
    @abstractmethod
    def scanpath(self, subject : Subject, trial : Trial, frequency : int) -> str:
        pass

    @abstractmethod
    def scanpathVideo(self, subject : Subject, trial : Trial, frequency : int, progress = None) -> str:
        pass

    @abstractmethod
    def createEyetracker(self, input_file: str) -> Eyetracker:
        pass

    def determineEyetracker(self, input_file: str) -> Eyetracker:
        for eyetracker in self.eyetrackers:
            if eyetracker.fits(input_file):
                return eyetracker
        eyetracker = self.createEyetracker(input_file)
        self.eyetrackers.append(eyetracker)
        return eyetracker

    def processSubject(self, input_file: str, progress_bar = None) -> Subject:
        eyetracker = self.determineEyetracker(input_file)
        subject = self.parseSubject(input_file, eyetracker, progress_bar)
        if self.isSubjectValid(subject):
            return subject
        else:
            raise ExperimentException('File %s does not fit the experiment' % input_file)

    def recalibrate(self, subject : Subject) -> None:
        pass

    @abstractmethod
    def parseSubject(self, input_file : str, progress_bar) -> Subject:
        pass

    @abstractmethod
    def makeResultFile() -> None:
        pass

    # Returns true if this subject made this experiment
    def isSubjectValid(self, subject : Subject) -> bool:
        if len(subject.trials) == 0:
            logTrace('Subject has no trial', Precision.ERROR)
            return False
        if self.expected_features == set():
            logTrace('Experiment has no expected features', Precision.ERROR)
            return False
        features = subject.trials[0].features.keys()
        if self.expected_features != features:
            logTrace('Expected features %s, got %s for trial 0' % (self.expected_features, features), Precision.ERROR)
            return False
        return True
