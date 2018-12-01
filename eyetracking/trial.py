from eyetracking.eyetracker import *
from eyetracking.interest_region import *
from typing import TypeVar, List
from math import sqrt, pow

class TrialException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

# Type of a line in the eyetracking result file
Line = List[str]

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

    def setEntries(self, lines: List[Line]) -> List[Line]:
        print('Trial: parsing entries')
        rest_lines = self.parseEntries(lines)
        print('Checking trial consistency')
        self.checkValid()
        print('Setting trial features')
        self.setFeatures()
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
    def parseEntries(self, lines : List[Line]) -> List[Line]:
        @match(Entry)
        class start(object):
            def Start_trial(a,b,c): return True
            def _(_): return False

        @match(Entry)
        class stop(object):
            def Stop_trial(_): return True
            def _(_): return False

        @match(Entry)
        class isBeginning(object):
            def Start_saccade(_): return True
            def Start_fixation(_): return True
            def Start_blink(_): return True
            def _(_): return False

        @match(Entry)
        class isSaccadeEnding(object):
            def End_saccade(_): return True
            def _(_): return False

        @match(Entry)
        class isFixationEnding(object):
            def End_fixation(_): return True
            def _(_): return False

        @match(Entry)
        class isBlinkEnding(object):
            def End_blink(_): return True
            def _(_): return False

        started = False
        begin = None
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

                    if isBeginning(entry):
                        begin = i
                    if begin is not None:
                        if isSaccadeEnding(entry):
                            self.saccades.append(Saccade(self, begin, i))
                            begin = None
                        if isFixationEnding(entry):
                            self.fixations.append(Fixation(self, begin, i))
                            begin = None
                        if isBlinkEnding(entry):
                            self.blinks.append(Blink(self, begin, i))
                            begin = None
        return []

    def setFeatures(self) -> None:
        @match(Entry)
        class getExperimentVariables(object):
            def Experiment_variables(_,variables): return variables
            def _(_): return None

        for entry in self.entries:
            variables = getExperimentVariables(entry)
            if variables != None:
                self.features = variables
                break

    # Returns the Start_trial entry of the trial.
    # The trial is assumed to be valid (see checkValid()).
    def getStartTrial(self) -> Entry:
        return self.entries[0]

    # Returns the Stop_trial entry of the trial.
    # The trial is assumed to be valid (see checkValid()).
    def getStopTrial(self) -> Entry:
        return self.entries[-1]

    def __str__(self):
        return 'Trial %s\n' % str(self.features)

    #Returns the line where the subject gives a manual response (or where the trial ends).
    def getResponse(self) -> Entry:
        @match(Entry)
        class isResponse(object):
            def Response(_): return True
            def _(_): return False

        for entry in self.entries:
            if isResponse(entry):
                return entry

        return self.getStopTrial()

    # Returns the trial id
    # The trial is assumed to be valid (see checkValid()).
    def getTrialId(self) -> int:
        @match(Entry)
        class getId(object):
            def Start_trial(time, trial_number, stimulus): return trial_number
            def _(_): return None

        return getId(self.getStartTrial())

    def getStartTrial(self) -> Entry:
        return self.entries[0]

    def getFixationTime(self, regions : InterestRegionList, target_region : InterestRegion):
        # Initializer of result type.
        def initialize_region_fixation():
            region_fixation = {}
            # First entry of the beginning
            region_fixation['begin'] = None
            # Last entry of the last fixation
            region_fixation['end'] = None
            # Region watched during fixations
            region_fixation['region'] = None
            # Total time on the regions
            region_fixation['time'] = None
            # Type of the fixations
            region_fixation['type'] = None
            # Boolean stating if the fixation happened on the target region
            region_fixation['target'] = None
            return region_fixation

        #Returns fixation type (normal, to the end of the trial, or too short)
        def set_type_fixation(region_fixation):
            region_fixation['type'] = "WRONG"
            if region_fixation['time'] != None and region_fixation['time'] != 0:
                region_fixation['type'] = "NORMAL"

            #We determine if the fixation is too short or not.
            if region_fixation['type'] != "WRONG" and region_fixation['time'] < 80:
                region_fixation['type'] = "SHORT"

        current_region_fixation = initialize_region_fixation()
        region_fixations = []

        # We create a copy to be able to remove elements
        blink_list = [blink for blink in self.blinks]

        for fixation in self.fixations:
            blink_encountered = False
            barycentre = fixation.barycentre()
            watched_region = regions.point_inside(barycentre)

            for blink in blink_list:
                if fixation.begin() > blink.end():
                    blink_list.remove(blink)
                    blink_encountered = True

            # If we find no corresponding frame, we determine the closer one. If its distance to the fixation is shorter enough, we take this frame.
            if closest_region == None:
                closest_region = regions.find_minimal_distance(barycentre)
                # maximum distance allowed between a point and a region
                max_dist = sqrt(pow(closest_region.half_width, 2) + pow(closest_region.half_height,2) + 30)
                if regions.distance(closest_region.center, barycentre) < max_dist:
                    watched_region = closest_region

            if current_region_fixation['begin'] == None and watched_region != None:
                current_region_fixation['begin'] = fixation.getEntry(fixation.get_begin())
                current_region_fixation['region'] = watched_region
                current_region_fixation['end'] = fixation.getEntry(fixation.get_end())

            # If we change of frame or encounter a blink, we end the previous fixation and add it to our list.
            if current_region_fixation['begin'] != None and watched_region != current_region_fixation['region'] or blink_encountered:
                current_region_fixation['time'] = current_region_fixation['end'].getTime() - current_region_fixation['begin'].getTime()
                set_type_fixation(current_region_fixation)
                current_region_fixation['target'] = (target_region == current_region_fixation['region'])

                if current_region_fixation['type'] == "NORMAL":
                    region_fixations.append(current_region_fixation)

                current_region_fixation = initialize_region_fixation()
            # If we already have a fixation and are still in it, we continue it and just change the ending point.
            elif current_region_fixation['begin'] != None and watched_region == current_region_fixation['region']:
                current_region_fixation['end'] = fixation.getEntry(fixation.get_end())

        # For the last region_fixation
        if current_region_fixation['begin'] != None:
            current_region_fixation['time'] = current_region_fixation['end'].getTime() - current_region_fixation['begin'].getTime()
            set_type_fixation(current_region_fixation)
            current_region_fixation['target'] = (target_region == current_region_fixation['region'])

            if current_region_fixation['type'] == "NORMAL":
                region_fixations.append(current_region_fixation)

        return region_fixations


class Subject:

    # list of training trials
    training_trials = []
    # TODO dissociate training and task

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

    def getTrial(self, trial_number : int):
        for trial in self.trials:
            if trial.getTrialId() == trial_number:
                return trial
        return None
