from eyetracking.eyetracker import *
from eyetracking.interest_region import *
from eyetracking.utils import *
from eyetracking.scanpath import plotSegment
from typing import TypeVar, List
from math import sqrt, pow

class TrialException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

# Type of a line in the eyetracking result file
Line = List[str]

class Trial:
    def __init__(self, experiment):
        # Experiment
        self.experiment = experiment
        # List of entries
        self.entries = []
        # Dictionary of trial features
        self.features = None
        # List of saccades
        self.saccades = []
        # List of fixations
        self.fixations = []
        # List of blinks
        self.blinks = []
        # Dominant eye.
        # Either "Left" or "Right"
        self.eye = None

        self.is_training = False

    def __str__(self):
        return 'Trial %s\n' % str(self.features)

    def printLines(self) -> None:
        for entry in self.entries:
            print(entry)

    def setEntries(self, lines: List[Line]) -> List[Line]:
        logTrace ('Parsing entries', Precision.NORMAL)
        rest_lines = self.parseEntries(lines)
        if not self.isEmpty():
            logTrace ('Checking trial validity', Precision.NORMAL)
            self.checkValid()
            logTrace ('Setting trial features', Precision.NORMAL)
            self.setFeatures()
            logTrace ('Setting eye', Precision.NORMAL)
            self.eye = self.experiment.eyetracker.getEye(lines)
            logTrace ('Setting if trial is training', Precision.NORMAL)
            self.is_training = self.experiment.eyetracker.isTraining(self)
        return rest_lines

    def isEmpty(self) -> bool:
        return self.entries == []

    def isTraining(self) -> bool:
        return self.is_training

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
        #Number of entries
        n_entries = 0
        i_line = -1
        for line in lines:
            i_line += 1
            entry = self.experiment.eyetracker.parseEntry(line)
            if entry != None:
                if start(entry):
                    started = True
                if started:
                    entry.check()
                    n_entries += 1
                    self.entries.append(entry)
                    #We are looking for entries with the same time as the stop trial entry
                    if stop(entry):
                        for line in lines[i_line + 1:]:
                            entry2 = self.experiment.eyetracker.parseEntry(line)
                            if entry2 != None and entry2.getTime() == entry.getTime():
                                self.entries.insert(len(self.entries)-1, entry2)
                            else:
                                break
                            i_line += 1
                        return lines[i_line + 1:]

                    if isBeginning(entry):
                        begin = n_entries - 1
                    if begin is not None:
                        if isSaccadeEnding(entry):
                            self.saccades.append(Saccade(self, begin, n_entries - 1))
                            begin = None
                        if isFixationEnding(entry):
                            self.fixations.append(Fixation(self, begin, n_entries - 1))
                            begin = None
                        if isBlinkEnding(entry):
                            self.blinks.append(Blink(self, begin, n_entries - 1))
                            begin = None
        return []

    def getFirstGazePosition(self) -> Union[Entry,None]:
        @match(Entry)
        class is_position(object):
            def Position(time,x,y) : return True
            def _(_) : return False

        for entry in self.entries:
            if is_position(entry):
                return entry

        return None

    def setFeatures(self) -> None:
        @match(Entry)
        class getExperimentVariables(object):
            def Experiment_variables(_,variables): return variables
            def _(_): return None

        self.features = {}
        for entry in self.entries:
            variables = getExperimentVariables(entry)
            if variables != None:
                for (key,value) in variables.items():
                    self.features[key] = value

    # Returns the Start_trial entry of the trial.
    # The trial is assumed to be valid (see checkValid()).
    def getStartTrial(self) -> Entry:
        return self.entries[0]

    # Returns the Stop_trial entry of the trial.
    # The trial is assumed to be valid (see checkValid()).
    def getStopTrial(self) -> Entry:
        return self.entries[-1]

    def getStimulus(self) -> str:
        @match(Entry)
        class get_stimulus(object):
            def Start_trial(time, trial_number, stimulus): return stimulus
            def _(_): return None

        res = get_stimulus(self.getStartTrial())
        if res == None:
            raise TrialException('Trial has no stimulus')

        return res

    #Returns the line where the subject gives a manual response (or where the trial ends).
    def getResponse(self) -> Union[Entry, None]:
        @match(Entry)
        class isResponse(object):
            def Response(_): return True
            def _(_): return False

        for entry in self.entries:
            if isResponse(entry):
                return entry

        return None

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

    def isStartValid(self, screen_center : Point, valid_distance_center : int) -> bool :
        @match(Entry)
        class is_end_saccade(object):
            def End_saccade(time): return True
            def _(_): return False
        @match(Entry)
        class is_position(object):
            def Position(time, x, y): return True
            def _(_): return False

        last_gaze_entry = None
        saccade_first = False
        # Check if a saccade had begun before the trial start
        for entry in self.entries[1:]:
            if is_end_saccade(entry):
                saccade_first = True
                break
            elif is_position(entry):
                last_gaze_entry = entry
            else:
                break

        if saccade_first:
            if distance(last_gaze_entry.getGazePosition(), screen_center) > valid_distance_center:
                return (False, last_gaze_entry.getGazePosition())
            else:
                return (True, last_gaze_entry.getGazePosition())
        first_pos = self.getFirstGazePosition()
        if first_pos == None or distance(first_pos.getGazePosition(), screen_center) > valid_distance_center:
            return (False, first_pos.getGazePosition())

        return (True, first_pos.getGazePosition())

    def getFixationTime(self, regions : InterestRegionList, target_region : InterestRegion, end_line = None):
        # end_line : line indicating the point where we are no longer interested in fixations.
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
        closest_region = None
        region_fixations = []

        # We create a copy to be able to remove elements
        blink_list = [blink for blink in self.blinks]

        for fixation in self.fixations:
            if (end_line is not None and fixation.begin < end_line) or end_line is None:
                blink_encountered = False
                barycentre = fixation.barycentre()
                watched_region = regions.point_inside(barycentre)

                for blink in blink_list:
                    if fixation.getStartTime() > blink.getEndTime():
                        blink_list.remove(blink)
                        blink_encountered = True
                        break

                # If we find no corresponding frame, we determine the closer one. If its distance to the fixation is shorter enough, we take this frame.
                if watched_region == None:
                    closest_region = regions.find_minimal_distance(barycentre)
                    # maximum distance allowed between a point and a region
                    max_dist = sqrt(pow(closest_region.half_width, 2) + pow(closest_region.half_height,2) + 30)
                    if distance(closest_region.center, barycentre) < max_dist:
                        watched_region = closest_region

                # If we change of frame or encounter a blink, we end the previous fixation and add it to our list.
                if current_region_fixation['begin'] != None and (watched_region != current_region_fixation['region'] or blink_encountered):
                    current_region_fixation['time'] = current_region_fixation['end'].getTime() - current_region_fixation['begin'].getTime()
                    set_type_fixation(current_region_fixation)
                    current_region_fixation['target'] = (target_region == current_region_fixation['region'])

                    if current_region_fixation['type'] == "NORMAL":
                        region_fixations.append(current_region_fixation)

                    current_region_fixation = initialize_region_fixation()

                if current_region_fixation['begin'] == None and watched_region != None:
                    current_region_fixation['begin'] = fixation.getEntry(fixation.getBegin())
                    current_region_fixation['region'] = watched_region
                    current_region_fixation['end'] = fixation.getEntry(fixation.getEnd())

                # If we already have a fixation and are still in it, we continue it and just change the ending point.
                elif current_region_fixation['begin'] != None and watched_region == current_region_fixation['region']:
                    current_region_fixation['end'] = fixation.getEntry(fixation.getEnd())

        # For the last region_fixation
        if current_region_fixation['begin'] != None:
            if end_line is not None:
                current_region_fixation['end'] = self.entries[end_line]
            current_region_fixation['time'] = current_region_fixation['end'].getTime() - current_region_fixation['begin'].getTime()
            set_type_fixation(current_region_fixation)
            current_region_fixation['target'] = (target_region == current_region_fixation['region'])

            if current_region_fixation['type'] == "NORMAL":
                region_fixations.append(current_region_fixation)

        return region_fixations

    def getGazePoints(self, end_line = None) -> List[Point] :
        @match(Entry)
        class isResponse(object):
            def Response(time) : return True
            def _(_): return False

        point_list = []
        for count, entry in enumerate(self.entries):
            if end_line is not None and count >= end_line:
                break
            if isResponse(entry):
                break
            else:
                point = entry.getGazePosition()
                if point is not None:
                    point_list.append(point)

        return point_list

    # Plot the trial on the current image
    def plot(self, frequency: int, end_line = None):

        nb_points = 0
        color = (1,1,0)

        point_list = self.getGazePoints(end_line)
        nb_points = float(len(point_list))

        for i in range(0,len(point_list)-frequency,frequency):
            plotSegment(point_list[i],point_list[i+frequency],c=color)
            color = (1, color[1] - float(frequency)/nb_points , 0)
