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
    def __init__(self, eyetracker):
        # Eyetracker
        self.eyetracker = eyetracker
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
        # Trial number
        self.id = None

        # Is the trial discarded
        self.discarded = False

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
            logTrace ('Setting trial features', Precision.NORMAL)
            self.setFeatures()
            logTrace ('Setting eye', Precision.NORMAL)
            self.eye = self.eyetracker.getEye(lines)
            logTrace ('Setting if trial is training', Precision.NORMAL)
            self.is_training = self.eyetracker.isTraining(self)
        return rest_lines

    def isEmpty(self) -> bool:
        for entry in self.entries:
            if isinstance(entry, Position):
                return False
        return True

    def isTraining(self) -> bool:
        return self.is_training

    # Raises an exception if one of the condition is not fulfilled.
    def checkValid(self) -> None:
        if self.entries == None:
            raise TrialException('Entries attribute is None')
        if type(self.entries) != list:
            raise TrialException('Entries attribute is not a list')
        if len(self.entries) < 2:
            raise TrialException('Entries attribute is too small')

        if not isinstance(self.entries[0], StartTrial):
            raise TrialException('First entry is not a start trial')
        if not isinstance(self.entries[-1], StopTrial):
            raise TrialException('Last entry is not a stop trial')

        for saccade in self.saccades:
            saccade.check()
        for fixation in self.fixations:
            fixation.check()
        for blink in self.blinks:
            blink.check()

    # Parses the given list of lines, to fill the entries attribute.
    # Return the rest of the lines
    def parseEntries(self, lines : List[Line]) -> List[Line]:
        #Number of entries
        begin_saccade = None
        begin_fixation = None
        begin_blink = None
        started = False
        i_line = -1
        for line in lines:
            i_line += 1
            entry = self.eyetracker.parseEntry(line)
            if entry != None:
                if isinstance(entry, StartTrial):
                    started = True
                    self.id = entry.trial_number
                if started:
                    entry.check()
                    self.entries.append(entry)
                    #We are looking for entries with the same time as the stop trial entry
                    if isinstance(entry, StopTrial):
                        for line in lines[i_line + 1:]:
                            entry2 = self.eyetracker.parseEntry(line)
                            if entry2 != None and entry2.getTime() == entry.getTime():
                                self.entries.insert(len(self.entries)-1, entry2)
                                if begin_saccade is not None and isinstance(entry2, EndSaccade):
                                    self.saccades.append(Saccade(self, begin_saccade, len(self.entries) - 2))
                                    begin_saccade = None
                                elif begin_fixation is not None and isinstance(entry2, EndFixation):
                                    self.fixations.append(Fixation(self, begin_fixation, len(self.entries) - 2))
                                    begin_fixation = None
                                elif begin_blink is not None and isinstance(entry2, EndBlink):
                                    self.blinks.append(Blink(self, begin_blink, len(self.entries) - 2))
                                    begin_blink = None
                            elif entry2 != None and entry2.getTime() != entry.getTime():
                                break
                            i_line += 1
                        return lines[i_line + 1:]

                    if isinstance(entry, StartSaccade):
                        begin_saccade = len(self.entries) - 1
                    elif isinstance(entry, StartFixation):
                        begin_fixation = len(self.entries) - 1
                    elif isinstance(entry, StartBlink):
                        begin_blink = len(self.entries) - 1

                    if begin_saccade is not None and isinstance(entry, EndSaccade):
                        self.saccades.append(Saccade(self, begin_saccade, len(self.entries) - 1))
                        begin_saccade = None
                    elif begin_fixation is not None and isinstance(entry, EndFixation):
                        self.fixations.append(Fixation(self, begin_fixation, len(self.entries) - 1))
                        begin_fixation = None
                    elif begin_blink is not None and isinstance(entry, EndBlink):
                        current_blink = Blink(self, begin_blink, len(self.entries) - 1)
                        if current_blink.isBlinkValid():
                            self.blinks.append(current_blink)
                        begin_blink = None
        return []

    def getFirstGazePosition(self) -> Union[Entry,None]:
        for entry in self.entries:
            if isinstance(entry, Position):
                return entry
        return None

    def setFeatures(self) -> None:
        self.features = {}
        for entry in self.entries:
            if isinstance(entry, TrialFeatures):
                for (k,v) in entry.features.items():
                    self.features[k] = v

    # Returns the Start_trial entry of the trial.
    # The trial is assumed to be valid (see checkValid()).
    def getStartTrial(self) -> Entry:
        return self.entries[0]

    # Returns the Stop_trial entry of the trial.
    # The trial is assumed to be valid (see checkValid()).
    def getStopTrial(self) -> Entry:
        return self.entries[-1]

    def getStimulus(self) -> str:
        return self.getStartTrial().stimulus

    #Returns the line where the subject gives a manual response (or where the trial ends).
    def getResponse(self) -> Union[Entry, None]:
        for entry in self.entries:
            if isinstance(entry, Response):
                return entry

        return None

    def discard(self, b) -> None:
        print('Discarding trial %i' % self.id)
        self.discarded = b

    def getStartTrial(self) -> Entry:
        return self.entries[0]

    def isStartValid(self, screen_center : Point, valid_distance_center : int) -> bool :
        last_gaze_entry = None
        saccade_first = False
        # Check if a saccade had begun before the trial start
        for entry in self.entries[1:]:
            if isinstance(entry, EndSaccade):
                saccade_first = True
                break
            elif isinstance(entry, Position):
                last_gaze_entry = entry
            else:
                break

        if saccade_first:
            if distance(last_gaze_entry.getGazePosition(), screen_center) > valid_distance_center:
                return (False, last_gaze_entry.getGazePosition())
            else:
                return (True, last_gaze_entry.getGazePosition())
        first_pos = self.getFirstGazePosition()
        if first_pos == None:
            return (False, None)
        elif distance(first_pos.getGazePosition(), screen_center) > valid_distance_center:
            return (False, first_pos.getGazePosition())


        return (True, first_pos.getGazePosition())

    def getFixationTime(self, regions : InterestRegionList, target_region : InterestRegion, end_line = None):
        """
        Returns the list of fixations that happen on the given regions.
        """
        # end_line : line indicating the point where we are no longer interested in fixations.
        # Initializer of result type.
        def initialize_region_fixation():
            fix = Fixation(self)
            # Region watched during fixations
            fix.region = None
            # Type of the fixations
            fix.type = None
            # Boolean stating if the fixation happened on the target region
            fix.on_target = None
            return fix

        #Returns fixation type (normal, to the end of the trial, or too short)
        def set_type_fixation(fix):
            fix.type = "WRONG"
            if fix.duration() > 0:
                if fix.duration() < 50: #30 for visual scenes, awaiting better with saccades
                    fix.type = "SHORT"
                else:
                    fix.type = "NORMAL"

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
                # if watched_region == None:
                #     closest_region = regions.find_minimal_distance(barycentre)
                #     # maximum distance allowed between a point and a region
                #     max_dist = sqrt(pow(closest_region.half_width, 2) + pow(closest_region.half_height,2)) + 10
                #     if distance(closest_region.center, barycentre) < max_dist:
                #         watched_region = closest_region

                # If we change of frame or encounter a blink, we end the previous fixation and add it to our list.
                if current_region_fixation.begin != None and (watched_region != current_region_fixation.region or blink_encountered):
                    set_type_fixation(current_region_fixation)
                    current_region_fixation.on_target = (target_region == current_region_fixation.region)

                    if current_region_fixation.type == "NORMAL":
                        region_fixations.append(current_region_fixation)

                    current_region_fixation = initialize_region_fixation()

                if current_region_fixation.begin == None and watched_region != None:
                    current_region_fixation.begin = fixation.getBegin()
                    current_region_fixation.region = watched_region
                    current_region_fixation.end = fixation.getEnd()

                # If we already have a fixation and are still in it, we continue it and just change the ending point.
                elif current_region_fixation.begin != None and watched_region == current_region_fixation.region:
                    current_region_fixation.end = fixation.getEnd()

        # For the last region_fixation
        if current_region_fixation.begin != None:
            if end_line is not None:
                current_region_fixation.end = end_line
            set_type_fixation(current_region_fixation)
            current_region_fixation.on_target = (target_region == current_region_fixation.region)

            if current_region_fixation.type == "NORMAL":
                region_fixations.append(current_region_fixation)

        if len(region_fixations) > 0:
            result = [region_fixations[0]]
            for reg in region_fixations[1:]:
                # Removed this part because fixations that we want merged are already merged before (fixations interspersed with saccades but all inside the same region). If we use the part below, it means that if two fixations on a same region are interspersed by a fixation that is not in an interest region (watched_region=None), they will be considered as the same fixation (e.g., AC06-7E trial 5)
                # if result[-1].region == reg.region:
                #     result[-1].merge(reg)
                # else:
                result.append(reg)
            return result
        else:
            return []

    def getGazePoints(self, end_line = None) -> List[Point] :
        point_list = []
        for count, entry in enumerate(self.entries):
            if end_line is not None and count >= end_line:
                break
            if isinstance(entry, Response):
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
