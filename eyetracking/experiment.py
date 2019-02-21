import attr
from abc import ABC, abstractmethod
from typing import List, Dict, Union

from eyetracking.subject import *

class ExperimentException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

class Experiment (ABC):

    def __init__(self, eyetracker):
        self.eyetracker = eyetracker
        self.expected_features = set()

    @abstractmethod
    def processTrial(self, subject : Subject, trial : Trial) -> None:
        pass

    # Creates an image scanpath for one trial.
    @abstractmethod
    def scanpath(self, subject_id : int, trial : Trial, frequency : int) -> str:
        pass

    @abstractmethod
    def scanpathVideo(self, subject_id : int, trial : Trial, frequency : int, progress = None) -> str:
        pass

    def processSubject(self, input_file: str, progress_bar = None) -> Subject:
        subject = self.parseSubject(input_file, progress_bar)
        if self.isSubjectValid(subject):
            return subject
        else:
            raise ExperimentException('File %s does not fit the experiment' % input_file)

    @abstractmethod
    def parseSubject(self, input_file : str, progress_bar) -> Subject:
        pass

    @abstractmethod
    def makeResultFile() -> None:
        pass

    # Returns true if this subject made this experiment
    def isSubjectValid(self, subject : Subject) -> bool:
        if len(subject.trials) == 0 or self.expected_features == set():
            return False
        features = subject.trials[0].features.keys()
        return self.expected_features == features
