import attr
from abc import ABC, abstractmethod
from typing import List, Dict, Union

from eyetracking.subject import *

class Experiment (ABC):

    def __init__(self, eyetracker):
        self.eyetracker = eyetracker

    @abstractmethod
    def processTrial(self, subject : Subject, trial : Trial) -> None:
        pass

    @abstractmethod
    def plotTarget(region: InterestRegion, cor_resp, color) -> None:
        pass

    # Creates an image scanpath for one trial.
    @abstractmethod
    def scanpath(self, trial : Trial) -> str:
        pass

    @abstractmethod
    def scanpathVideo(self, trial : Trial):
        pass

    @abstractmethod
    def processSubject(self, input_file: str, progress_bar = None) -> Subject:
        pass
