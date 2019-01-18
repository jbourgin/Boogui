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

    @abstractmethod
    def processTrial(self, subject : Subject, trial : Trial) -> None:
        pass

    # Creates an image scanpath for one trial.
    @abstractmethod
    def scanpath(self, subject_id : int, trial : Trial, frequency : int) -> str:
        pass

    @abstractmethod
    def scanpathVideo(self, subject_id : int, trial : Trial):
        pass

    @abstractmethod
    def processSubject(self, input_file: str, progress_bar = None) -> Subject:
        pass

    @abstractmethod
    def makeResultFile() -> None:
        pass
