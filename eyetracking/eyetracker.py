import attr
from abc import ABC, abstractmethod
from typing import List, Dict

from eyetracking.entry import *

class Experiment:

    def __init__(self, eyetracker):
        self.eyetracker = eyetracker
        
    # Returns a dictionary of experiment variables
    @abstractmethod
    def parseVariables(line: List[str]):
        pass

    @abstractmethod
    def isResponse(line: List[str]) -> bool:
        pass

    @abstractmethod
    def isTraining(trial) -> bool:
        pass

class EyetrackerInterface:

    def __init__(self):
        pass

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

    @abstractmethod
    def isTraining(self, trial) -> bool:
        pass
