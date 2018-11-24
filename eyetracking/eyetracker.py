import attr
from abc import ABC, abstractmethod
from typing import List, Dict

from eyetracking.entry import *

class Experiment:
    # Returns a dictionary of experiment variables
    @abstractmethod
    def parseVariables(line: List[str]):
        pass

    @abstractmethod
    def isResponse(line: List[str]) -> bool:
        pass

class EyetrackerInterface:

    experiment = None

    def __init__(self, experiment):
        self.experiment = experiment

    @abstractmethod
    def parseEntry(line: List[str]) -> Entry:
        pass

    @abstractmethod
    def getEye(lines: List[List[str]]) -> str:
        pass

    # return True if the given file has been recorded with this eyetracker
    @abstractmethod
    def isParsable(filename : str) -> bool:
        pass
