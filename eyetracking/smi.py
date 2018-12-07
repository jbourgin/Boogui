from eyetracking.trial import *
from eyetracking.eyelink import Eyelink
from eyetracking.smi_correction import processSubject

class Smi (Eyetracker):

    def __init__(self):
        super().__init__()

    @staticmethod
    def getEye(lines: List[List[str]]) -> str:
        for line in lines:
            if len(line) > 1 and line[1] == "L":
                return "LEFT"
            elif len(line) > 1 and line[1] == "R":
                return "RIGHT"
        return None

    @staticmethod
    def isParsable(filename : str) -> bool:
        return not Eyelink.isParsable(filename)

    #######################################
    ############ ENTRY PARSERS ############
    #######################################
    # Each of the following parser tries to parse one type of Entry
    # If is fails, it returns None

    @staticmethod
    def parseStartTrial(line: List[str]) -> Entry:
        if len(line) >= 8 and line[5] == 'start_trial':
            try:
                time = int(line[0])
                trial_number = int(line[6])
                stimulus = line[7]
                return Entry.Start_trial(time, trial_number, stimulus)
            except:
                pass
        return None

    @staticmethod
    def parseStopTrial(line: List[str]) -> Entry:
        if len(line) >= 6 and line[5] == 'stop_trial':
            try:
                time = int(line[0])
                return Entry.Stop_trial(time)
            except:
                pass
        return None

    @staticmethod
    def parsePosition(line: List[str]) -> Entry:
        # case Position
        if len(line) >= 5:
            try:
                time = int(line[0])
                x = float(line[3])
                y = float(line[4])
                return Entry.Position(time, x, y)
            except:
                pass
        return None

    @staticmethod
    def parseStartFixation(line: List[str]) -> Entry:
        # case Position
        if len(line) >= 3 and line[0] == 'SFIX':
            try:
                time = int(line[2])
                return Entry.Start_fixation(time)
            except:
                pass
        return None

    @staticmethod
    def parseEndFixation(line: List[str]) -> Entry:
        # case Position
        if len(line) >= 4 and line[0] == 'EFIX':
            try:
                time = int(line[3])
                return Entry.End_fixation(time)
            except:
                pass
        return None

    @staticmethod
    def parseStartBlink(line: List[str]) -> Entry:
        # case Position
        if len(line) >= 3 and line[0] == 'SBLINK':
            try:
                time = int(line[2])
                return Entry.Start_blink(time)
            except:
                pass
        return None

    @staticmethod
    def parseEndBlink(line: List[str]) -> Entry:
        # case Position
        if len(line) >= 4 and line[0] == 'EBLINK':
            try:
                time = int(line[3])
                return Entry.End_blink(time)
            except:
                pass
        return None

    @staticmethod
    def parseStartSaccade(line: List[str]) -> Entry:
        # case Position
        if len(line) >= 3 and line[0] == 'SSACC':
            try:
                time = int(line[2])
                return Entry.Start_saccade(time)
            except:
                pass
        return None

    @staticmethod
    def parseEndSaccade(line: List[str]) -> Entry:
        # case Position
        if len(line) >= 4 and line[0] == 'ESACC':
            try:
                time = int(line[3])
                return Entry.End_saccade(time)
            except:
                pass
        return None

    def parseResponse(self, line: List[str]) -> Entry:
        # case Position
        print(line)
        if self.isResponse(line):
            try:
                time = int(line[0])
                return Entry.Response(time)
            except:
                pass
        return None

    @abstractmethod
    def isResponse(self, line : Line) -> bool:
        pass

    def parseExperimentVariables(self, line: List[str]) -> Entry:
        # case Position
        print(line)
        try:
            time = int(line[0])
            variables = self.parseVariables(line)
            return Entry.Experiment_variables(time, variables)
        except:
            return None

    @abstractmethod
    def parseVariables(self, line: Line):
        pass

    def parseEntry(self, line: List[str]) -> Entry:
        parsers = [Smi.parseStartTrial,
            Smi.parseStopTrial,
            Smi.parsePosition,
            Smi.parseStartFixation,
            Smi.parseEndFixation,
            Smi.parseStartBlink,
            Smi.parseEndBlink,
            Smi.parseStartSaccade,
            Smi.parseEndSaccade,
            self.parseResponse,
            self.parseExperimentVariables]

        for parser in parsers:
            res = parser(line)
            if res != None:
                return res

        return None

    def preprocess(self, input_file: str, output_file: str) -> bool:
        processSubject(input_file, output_file)
        return True
