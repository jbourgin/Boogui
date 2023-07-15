import attr
import re #To format data lists
import pandas as pd
from abc import ABC, abstractmethod
from typing import List, Dict, Union, Set

from eyetracking.utils import *
from eyetracking.subject import *
from eyetracking.entry import *

class Col():

    # Columns constants
    SUBJID = "Subject"
    GROUP = "Group"
    TRIALID = "TrialID"
    EYE = "Eye"
    BLINK = "First blink type"

class ExperimentException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

class Experiment (ABC):

    def __init__(self, expected_features: Set[str], exp_name):
        self.expected_features = expected_features
        self.dataframe = None
        self.exp_name = os.path.basename(os.path.splitext(exp_name)[0])

    def processSubject(self, input_file: str, progress_bar = None) -> "Subject":
        subject = self.parseSubject(input_file, progress_bar)
        if self.isSubjectValid(subject):
            return subject
        else:
            raise ExperimentException('File %s does not fit the experiment' % input_file)

    # Returns true if this subject made this experiment
    def isSubjectValid(self, subject : "Subject") -> bool:
        if len(subject.trials) == 0:
            logTrace('Subject has no trial', Precision.ERROR)
            return False
        if self.expected_features == set():
            logTrace('Experiment has no expected features', Precision.ERROR)
            return False
        for trial in subject.trials:
            features = trial.features.keys()
            if self.expected_features == features:
                return True
        # If no trial has expected features
        logTrace('Expected features %s, got %s for trial 0' % (self.expected_features, features), Precision.ERROR)
        return False

    @staticmethod
    def getEye(lines: List[List[str]]) -> str:
        for line in lines:
            if len(line) > 2 and line[0] == "SSACC":
                return line[1]
        return None

    #######################################
    ############ ENTRY PARSERS ############
    #######################################
    # Each of the following parser tries to parse one type of Entry
    # If is fails, it returns None

    def parseStartTrial(self, line: List[str]) -> Union[Entry, None]:
        if len(line) >= 5 and line[2] == 'start_trial':
            try:
                time = int(line[1])
                trial_number = int(line[3])
                stimulus = ''.join(line[4:])
                return StartTrial(time, trial_number, stimulus)
            except:
                pass
        return None

    def parseStopTrial(self, line: List[str]) -> Union[Entry, None]:
        if len(line) >= 3 and line[2] == 'stop_trial':
            try:
                time = int(line[1])
                return StopTrial(time)
            except:
                pass
        return None

    def parsePosition(self, line: List[str]) -> Union[Entry, None]:
        # case Position
        if len(line) >= 3:
            try:
                time = int(line[0])
                x = float(line[1])
                y = float(line[2])
                return Position(time, x, y)
            except:
                pass
        return None

    def parseStartFixation(self, line: List[str]) -> Union[Entry, None]:
        # case Position
        if len(line) >= 3 and line[0] == 'SFIX':
            try:
                time = int(line[2])
                return StartFixation(time)
            except:
                pass
        return None

    def parseEndFixation(self, line: List[str]) -> Union[Entry, None]:
        # case Position
        if len(line) >= 4 and line[0] == 'EFIX':
            try:
                time = int(line[3])
                return EndFixation(time)
            except:
                pass
        return None

    def parseStartBlink(self, line: List[str]) -> Union[Entry, None]:
        # case Position
        if len(line) >= 3 and line[0] == 'SBLINK':
            try:
                time = int(line[2])
                return StartBlink(time)
            except:
                pass
        return None

    def parseEndBlink(self, line: List[str]) -> Union[Entry, None]:
        # case Position
        if len(line) >= 4 and line[0] == 'EBLINK':
            try:
                time = int(line[3])
                return EndBlink(time)
            except:
                pass
        return None

    def parseStartSaccade(self, line: List[str]) -> Union[Entry, None]:
        # case Position
        if len(line) >= 3 and line[0] == 'SSACC':
            try:
                time = int(line[2])
                return StartSaccade(time)
            except:
                pass
        return None

    def parseEndSaccade(self, line: List[str]) -> Union[Entry, None]:
        # case Position
        if len(line) >= 4 and line[0] == 'ESACC':
            try:
                time = int(line[3])
                return EndSaccade(time)
            except:
                pass
        return None

    def parseResponse(self, line: Line) -> Union[Entry, None]:
        # case Position
        if self.isResponse(line):
            try:
                time = int(line[1])
                return Response(time)
            except:
                pass
        return None

    def parseExperimentVariables(self, line: List[str]) -> Union[Entry, None]:
        # case Position
        try:
            time = int(line[1])
            variables = self.parseVariables(line)
            if variables != None:
                return TrialFeatures(time, variables)
            else:
                return None
        except:
            return None

    def parseMessage(self, line: Line) -> Union[Entry, None]:
        try:
            time = int(line[1])
            message = ' '.join(line[2:])
            return Message(time, message)
        except:
            return None


    def parseEntry(self, line: List[str]) -> Union[Entry, None]:
        parsers = [self.parseStartTrial,
            self.parseStopTrial,
            self.parsePosition,
            self.parseStartFixation,
            self.parseEndFixation,
            self.parseStartBlink,
            self.parseEndBlink,
            self.parseStartSaccade,
            self.parseEndSaccade,
            self.parseResponse,
            self.parseExperimentVariables,
            self.parseMessage]

        for parser in parsers:
            res = parser(line)
            if res != None:
                return res

        return None

    # TODO: no need for abstract: factorize?
    def getSubjectData(self, line: str) -> Union[Tuple[int,str]]:
        try:
            l = re.split('[\t ]+', line)
            return (int(l[1]), l[2])
        except:
            return None

    def parseSubject(self, input_file : str, progress = None) -> Subject:

        with open(input_file) as f:
            first_line = f.readline()
            if first_line[-1] == '\n':
                first_line = first_line[:-1]

        subject_data = self.getSubjectData(first_line)

        if subject_data is None:
            raise ExperimentException('Subject number and category could not be found')

        else:
            result_file = 'results.txt'
            datafile = open(input_file, 'r')

            #File conversion in list.
            data = datafile.read()
            data = list(data.splitlines())

            #We add a tabulation and space separator.
            data = [re.split('[\t ]+',line) for line in data]

            (n_subject, subject_cat) = subject_data
            return Subject(self, self.n_trials, data, n_subject, subject_cat, progress)

    ##########################################
    ############ Abstract methods ############
    ##########################################
    @abstractmethod
    def isResponse(self, line : Line) -> bool:
        pass

    @abstractmethod
    def isTraining(self, trial) -> bool:
        pass

    @abstractmethod
    def parseVariables(self, line: Line):
        """
        Returns a dictionary of experiment variables
        """
        pass

    def processTrial(self, subject : "Subject", trial : Trial) -> None:
        logTrace ('Processing trial n°%i' % trial.id, Precision.DETAIL)

        self.trial_dict = {
            Col.SUBJID: "%i-E"%subject.id,
            Col.GROUP: subject.group,
            Col.TRIALID: trial.id,
            Col.EYE: trial.eye,
        }

    # Creates an image scanpath for one trial.
    @abstractmethod
    def scanpath(self, subject : "Subject", trial : Trial, frequency : int) -> str:
        pass

    @abstractmethod
    def scanpathVideo(self, subject : "Subject", trial : Trial, frequency : int, progress = None) -> str:
        pass
