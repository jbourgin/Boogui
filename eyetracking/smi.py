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
                return "L"
            elif len(line) > 1 and line[1] == "R":
                return "R"
        return None

    @staticmethod
    def isParsable(filename : str) -> bool:
        with open(filename) as file:
            line = file.readline()
            n = 0
            while line:
                if n >= 100: return False
                if 'IDF Converter' in line: return True
                line = file.readline()
                n += 1
        return False

    #######################################
    ############ ENTRY PARSERS ############
    #######################################
    # Each of the following parser tries to parse one type of Entry
    # If is fails, it returns None

    def parseStartTrial(self, line: List[str]) -> Entry:
        if len(line) >= 8 and line[5] == 'start_trial':
            try:
                time = int(line[0])
                trial_number = int(line[6])
                stimulus = line[7] + line[8]
                return StartTrial(time, trial_number, stimulus)
            except:
                pass
        return None

    def parseStopTrial(self, line: List[str]) -> Entry:
        if len(line) >= 6 and line[5] == 'stop_trial':
            try:
                time = int(line[0])
                return StopTrial(time)
            except:
                pass
        return None

    def parsePosition(self, line: List[str]) -> Entry:
        if len(line) >= 5:
            try:
                time = int(line[0])
                x = float(line[3])
                y = float(line[4])
                return Position(time, x, y)
            except:
                pass
        return None

    def parseStartFixation(self, line: List[str]) -> Entry:
        if len(line) >= 3 and line[0] == 'SFIX':
            try:
                time = int(line[2])
                return StartFixation(time)
            except:
                pass
        return None

    def parseEndFixation(self, line: List[str]) -> Entry:
        if len(line) >= 4 and line[0] == 'EFIX':
            try:
                time = int(line[3])
                return EndFixation(time)
            except:
                pass
        return None

    def parseStartBlink(self, line: List[str]) -> Entry:
        if len(line) >= 3 and line[0] == 'SBLINK':
            try:
                time = int(line[2])
                return StartBlink(time)
            except:
                pass
        return None

    def parseEndBlink(self, line: List[str]) -> Entry:
        if len(line) >= 4 and line[0] == 'EBLINK':
            try:
                time = int(line[3])
                return EndBlink(time)
            except:
                pass
        return None

    def parseStartSaccade(self, line: List[str]) -> Entry:
        if len(line) >= 3 and line[0] == 'SSACC':
            try:
                time = int(line[2])
                return StartSaccade(time)
            except:
                pass
        return None

    def parseEndSaccade(self, line: List[str]) -> Entry:
        if len(line) >= 4 and line[0] == 'ESACC':
            try:
                time = int(line[3])
                return EndSaccade(time)
            except:
                pass
        return None

    def parseResponse(self, line: List[str]) -> Entry:
        if self.isResponse(line):
            try:
                time = int(line[0])
                return Response(time)
            except:
                pass
        return None

    @abstractmethod
    def isResponse(self, line : Line) -> bool:
        pass

    def parseExperimentVariables(self, line: List[str]) -> Entry:
        try:
            time = int(line[0])
            variables = self.parseVariables(line)
            return TrialFeatures(time, variables)
        except:
            return None

    @abstractmethod
    def parseVariables(self, line: Line):
        pass

    def parseMessage(self, line: Line):
        return None

    def parseEntry(self, line: List[str]) -> Entry:
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

    def preprocess(self, input_file: str, output_file: str, progress_bar = None) -> bool:
        processSubject(input_file, output_file, progress_bar)
        return True
