from eyetracker import *

class TrialException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

class Trial:
    # List of entries
    entries = []

    # Dictionary of trial features
    features = None

    # Eyetracker that implements EyetrackerInterface
    eyetracker = None

    # List of saccades
    saccades = []

    # List of fixations
    fixations = []

    # List of blinks
    blinks = []

    # Dominant eye.
    # Either "Left" or "Right"
    eye = None

    def __init__(self, eyetracker):
        self.eyetracker = eyetracker

    def setEntries(self, lines: List[List[str]]) -> List[List[str]]:
        print('Trial: parsing entries')
        rest_lines = self.parseEntries(lines)
        print('Checking trial consistency')
        self.checkValid()
        print('Setting trial features')
        self.setFeatures()
        print('Parsing trial saccades')
        self.parseSaccades()
        print('Parsing trial fixations')
        self.parseFixations()
        print('Parsing trial blinks')
        self.parseBlinks()
        print('Setting dominant eye')
        self.eye = self.eyetracker.getEye(lines)
        return rest_lines

    def isEmpty(self) -> bool:
        return self.entries == []

    # Raises an exception if one of the condition is not fulfilled.
    def checkValid(self) -> None:
        @match(Entry)
        class checkStart(object):
            def Start_trial(a,b,c): pass
            def _(_): raise TrialException('First entry is not a start trial')
        @match(Entry)
        class checkEnd(object):
            def Stop_trial(_): pass
            def _(_): raise TrialException('Last entry is not a stop trial')

        if self.entries == None:
            raise TrialException('Entries attribute is None')
        if type(self.entries) != list:
            raise TrialException('Entries attribute is not a list')
        if len(self.entries) < 2:
            raise TrialException('Entries attribute is too small')

        checkStart(self.entries[0])
        checkEnd(self.entries[len(self.entries) - 1])

    # Parses the given list of lines, to fill the entries attribute.
    # Return the rest of the lines
    def parseEntries(self,lines) -> List[List[str]]:
        @match(Entry)
        class start(object):
            def Start_trial(a,b,c): return True
            def _(_): return False

        @match(Entry)
        class stop(object):
            def Stop_trial(_): return True
            def _(_): return False

        started = False
        i = -1
        for line in lines:
            i += 1
            entry = self.eyetracker.parseEntry(line)
            if entry != None:
                if start(entry):
                    started = True
                if started:
                    entry.check()
                    self.entries.append(entry)
                    if stop(entry): return lines[i+1:]
        return []

    def setFeatures(self):
        @match(Entry)
        class getExperimentVariables(object):
            def Experiment_variables(_,variables): return variables
            def _(_): return None

        for entry in self.entries:
            variables = getExperimentVariables(entry)
            if variables != None:
                self.features = variables
                break

    def parseSaccades(self) -> None:
        @match(Entry)
        class isSaccadeBeginning(object):
            def Start_saccade(_): return True
            def _(_): return False

        @match(Entry)
        class isSaccadeEnding(object):
            def End_saccade(_): return True
            def _(_): return False

        began = False
        entries = []
        for entry in self.entries:
            if isSaccadeBeginning(entry):
                began = True
            if began:
                entries.append(entry)
                if isSaccadeEnding(entry):
                    began = False
                    self.saccades.append(Saccade(entries))
                    entries = []

    def parseFixations(self) -> None:
        @match(Entry)
        class isFixationBeginning(object):
            def Start_fixation(_): return True
            def _(_): return False

        @match(Entry)
        class isFixationEnding(object):
            def End_fixation(_): return True
            def _(_): return False

        began = False
        entries = []
        for entry in self.entries:
            if isFixationBeginning(entry):
                began = True
            if began:
                entries.append(entry)
                if isFixationEnding(entry):
                    began = False
                    self.fixations.append(Fixation(entries))
                    entries = []

    def parseBlinks(self) -> None:
        @match(Entry)
        class isBlinkBeginning(object):
            def Start_blink(_): return True
            def _(_): return False

        @match(Entry)
        class isBlinkEnding(object):
            def End_blink(_): return True
            def _(_): return False

        began = False
        entries = []
        for entry in self.entries:
            if isBlinkBeginning(entry):
                began = True
            if began:
                entries.append(entry)
                if isBlinkEnding(entry):
                    began = False
                    self.blinks.append(Blink(entries))
                    entries = []

    # Returns the Start_trial entry of the trial.
    # The trial is assumed to be valid (see checkValid()).
    def getStartTrial(self) -> Entry:
        return self.entries[0]

    # Returns the Stop_trial entry of the trial.
    # The trial is assumed to be valid (see checkValid()).
    def getStopTrial(self) -> Entry:
        return self.entries[-1]

    def __str__(self):
        return 'Trial %s\n%s\nsaccades: %s\nfixations: %s' % (
            str(self.features),
            '\n'.join([str(entry) for entry in self.entries]),
            self.saccades,
            self.fixations)

    #Returns the line where the subject gives a manual response (or where the trial ends).
    def get_response(self, trial):
        @match(Entry)
        class isResponse(object):
            def Response(_): return True
            def _(_): return False

        for entry in self.entries:
            if isResponse(entry):
                return entry

        return self.getStopTrial()

    #Returns the trial id
    # The trial is assumed to be valid (see checkValid()).
    def getTrialId(self):
        @match(Entry)
        class getId(object):
            def Start_trial(time, trial_number, stimulus): return trial_number
            def _(_): return None

        return getId(self.getStartTrial())

class Subject:

    # list of trials
    trials = []

    subject_number = None

    def __init__(self, eyetracker, lines):
        while lines != []:
            print('nombre de lignes à traiter : %i' % len(lines))
            trial = Trial(eyetracker)
            lines = trial.setEntries(lines)
            if not trial.isEmpty():
                self.trials.append(trial)
