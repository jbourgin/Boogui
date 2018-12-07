import attr
from abc import ABC, abstractmethod
from typing import List, Dict, Union

from eyetracking.entry import *

class Eyetracker (ABC):

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

    @abstractmethod
    def parseEntry(line: List[str]) -> Union[Entry, None]:
        pass

    # Returns a dictionary of experiment variables
    @abstractmethod
    def parseVariables(line: List[str]) -> Union[Entry, None]:
        pass

    @abstractmethod
    def isResponse(line: List[str]) -> bool:
        pass

    @abstractmethod
    def preprocess(self, input_file: str, output_file: str) -> bool:
        pass
