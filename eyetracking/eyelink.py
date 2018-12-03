from eyetracking.trial import *

class Eyelink (EyetrackerInterface):

    def __init__(self):
        super().__init__()

    @staticmethod
    def getEye(lines: List[List[str]]) -> str:
        for line in lines:
            if len(line) > 2 and line[0] == "SSACC":
                return line[1]
        return None

    @staticmethod
    def isParsable(filename : str) -> bool:
        with open(filename) as file:
            line = file.readline()
            n = 0
            while line:
                if n >= 100: return False
                if 'EYELINK' in line: return True
                line = file.readline()
                n += 1
        return False

    #######################################
    ############ ENTRY PARSERS ############
    #######################################
    # Each of the following parser tries to parse one type of Entry
    # If is fails, it returns None

    @staticmethod
    def parseStartTrial(line: List[str]) -> Entry:
        if len(line) >= 7 and line[2] == 'start_trial':
            try:
                time = int(line[1])
                trial_number = int(line[3])
                stimulus = ''.join(line[4:])
                return Entry.Start_trial(time, trial_number, stimulus)
            except:
                pass
        return None

    @staticmethod
    def parseStopTrial(line: List[str]) -> Entry:
        if len(line) >= 3 and line[2] == 'stop_trial':
            try:
                time = int(line[1])
                return Entry.Stop_trial(time)
            except:
                pass
        return None

    @staticmethod
    def parsePosition(line: List[str]) -> Entry:
        # case Position
        if len(line) >= 3:
            try:
                time = int(line[0])
                x = float(line[1])
                y = float(line[2])
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

    def parseResponse(self, line: Line) -> Entry:
        # case Position
        if self.isResponse(line):
            try:
                time = int(line[1])
                return Entry.Response(time)
            except:
                pass
        return None

    @abstractmethod
    def isResponse(self, line : Line) -> bool:
        pass

    def parseExperimentVariables(self, line: List[str]) -> Entry:
        # case Position
        try:
            time = int(line[1])
            variables = self.parseVariables(line)
            return Entry.Experiment_variables(time, variables)
        except:
            return None

    @abstractmethod
    def parseVariables(self, line: Line):
        pass

    def parseEntry(self, line: List[str]) -> Entry:
        parsers = [Eyelink.parseStartTrial,
            Eyelink.parseStopTrial,
            Eyelink.parsePosition,
            Eyelink.parseStartFixation,
            Eyelink.parseEndFixation,
            Eyelink.parseStartBlink,
            Eyelink.parseEndBlink,
            Eyelink.parseStartSaccade,
            Eyelink.parseEndSaccade,
            self.parseResponse,
            self.parseExperimentVariables]

        for parser in parsers:
            res = parser(line)
            if res != None:
                return res

        return None
