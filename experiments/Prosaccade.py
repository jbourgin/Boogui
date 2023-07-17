from eyetracking.experiment import *
from eyetracking.interest_region import *
from PyQt5.QtWidgets import QApplication

class PSCol(Col):

    # Specific columns
    EMOTION = "Emotion"
    TARGET = "Target Name"
    SIDE = "Target Side"
    COR_POS = "Correct position"
    ERR = "Errors"
    FIRST_RT = "First saccade RT"
    FIRST_POS_START = "First saccade start gaze position"
    FIRST_POS_END = "First saccade ending gaze position"
    FIRST_DUR = "First saccade duration"
    THRESH = "Threshold excess"
    TRAINING = "Training"

class Exp(Experiment):

    def __init__(self):
        super().__init__({'training', 'target_side'}, __file__)
        self.n_trials = 96
        self.screen_center = (512,384)
        # Minimal distance at which we consider the subject is looking at the
        # fixation cross at the trial beginning
        self.valid_distance_center = 90 #3 degres of visual angle 95 (+ marge)

        # Initializing regions of interest
        self.half_width = 128 #170
        self.half_height = 128 #170

        # frames
        self.right = RectangleRegion((self.screen_center[0]*1.5, self.screen_center[1]), self.half_width, self.half_height)
        self.left = RectangleRegion((self.screen_center[0]/2, self.screen_center[1]), self.half_width, self.half_height)

        # For postProcess
        self.IVs = [
            PSCol.EMOTION
        ]

        self.DVs = [
            PSCol.FIRST_RT
        ]

    ###############################################
    ############## Overriden methods ##############
    ###############################################

    # Returns a dictionary of experiment variables
    def parseVariables(self, line: List[str]):
        if len(line) >= 5 and line[2] == 'BEGIN' and line[3] == 'SEQUENCE':
            try:
                training = line[5][:-6]
                target_side = line[5][-6:]

                return {
                    'training' : training,
                    'target_side' : target_side,
                }
            except:
                pass
        return None

    def parseStartTrial(self, line: List[str]) -> Union[Entry, None]:
        if len(line) >= 4 and line[2] == 'BEGIN' and line[3] == 'TRANSITION' and line[4] == 'time_transition':
            try:
                time = int(line[1])
                trial_number = int(line[-1])
                stimulus = line[10]
                return StartTrial(time, trial_number, stimulus)
            except:
                pass
        return None

    def isTraining(self, trial) -> bool:
        return 'App' in trial.features['training']

    def isResponse(self, line: Line) -> bool :
        return len(line) >= 5 and 'END' in line[2] and 'TRANSITION' in line[3] and 'TIMEOUT' in line[4]

    def parseStopTrial(self, line: List[str]) -> Union[Entry, None]:
        if len(line) >= 4 and line[2] == 'END' and line[3] == 'SEQUENCE':
            try:
                time = int(line[1])
                return StopTrial(time)
            except:
                pass
        return None

    ######################################################
    ############## End of Overriden methods ##############
    ######################################################

    def processTrial(self, subject: Subject, trial):
        super().processTrial(subject, trial)
        targetname = trial.getStimulus()

        if trial.saccades == []:
            logTrace ('Subject %i has no saccades at trial %i !' %(subject.id, trial.id), Precision.DETAIL)
        else:
            if trial.features['target_side'] == 'Gauche':
                correct_position = 'Left'
                target_position = self.left
            elif trial.features['target_side'] == 'Droite':
                correct_position = 'Right'
                target_position = self.right

            start_trial_time = trial.getStartTrial().getTime()

            if 'Neg' in targetname[:3]:
                emotion = 'Negative'
            elif 'P' in targetname[0]:
                emotion = 'Positive'
            elif 'Neu' in targetname[:3]:
                emotion = 'Neutral'
            else:
                emotion = 'Training'

            # First saccade
            SRT_real = trial.saccades[0].getStartTime() - start_trial_time
            sac_duration = trial.saccades[0].getEndTime() - trial.saccades[0].getStartTime()
            sac_amplitude = distance(trial.saccades[0].getFirstGazePosition(), trial.saccades[0].getLastGazePosition())
            horizontal_gaze_position_end = trial.saccades[0].getLastGazePosition()[0]
            SRT_threshold = SRT_real + sac_duration

            if SRT_real > 500:
                threshold_excess = 'YES'
            else:
                threshold_excess = 'NO'

            # Determining blink category
            if trial.blinks == []:
                blink_category = 'No blink'
            else:
                if trial.blinks[0].getStartTime() < SRT_threshold:
                    blink_category = 'early capture'
                else:
                    blink_category = 'late'

            # Error :
            if not trial.isStartValid(self.screen_center, self.valid_distance_center)[0]:
                error = ERROR.START_INVALID
            elif blink_category == 'early capture':
                error = ERROR.EARLY_BLINK
            elif SRT_real <= 80:
                error = ERROR.EARLY_SACCADE
            elif sac_duration < 22:
                error = ERROR.SHORT_SACCADE
            elif sac_amplitude < self.valid_distance_center:
                error = ERROR.MICRO_SACCADE
            elif ((correct_position == 'Right'
                  and horizontal_gaze_position_end < self.screen_center[0])
                  or (correct_position == 'Left'
                      and horizontal_gaze_position_end > self.screen_center[0])):
                error = '1'
            elif ((correct_position == 'Right'
                  and horizontal_gaze_position_end > self.screen_center[0])
                  or (correct_position == 'Left'
                      and horizontal_gaze_position_end < self.screen_center[0])):
                error = '0'
            else:
                error = None

            # Writing data in result csv file
            new_dict = {
                PSCol.TRAINING: trial.features['training'],
                PSCol.EMOTION: emotion,
                PSCol.TARGET: targetname,
                PSCol.SIDE: trial.features['target_side'],
                PSCol.COR_POS: correct_position,
                PSCol.ERR: error,
                PSCol.FIRST_RT: trial.saccades[0].getStartTime() - start_trial_time,
                PSCol.FIRST_POS_START: trial.saccades[0].getFirstGazePosition(),
                PSCol.FIRST_POS_END: trial.saccades[0].getLastGazePosition(),
                PSCol.FIRST_DUR: trial.saccades[0].getEndTime() - trial.saccades[0].getStartTime(),
                PSCol.BLINK: blink_category,
                PSCol.THRESH: threshold_excess
            }

            self.updateDict(new_dict)

    def isEligibleTrial(self, trial, DV):
        if DV == PSCol.FIRST_RT:
            # Exclude trials with no saccade and trials with error or non desired events (blink, anticipation, etc.)
            return super().isEligibleTrial(trial, DV) and trial[PSCol.FIRST_RT] != None and trial[PSCol.ERR] == "0"
        return True

    ######################################################
    ###################### Plot data #####################
    ######################################################

    # Get frame color (stim delimitation during scanpath plot)
    def getFrameColor(self, trial):
        if 'P' in trial.getStimulus()[0]:
            return (0,1,0)
        elif 'Neg' in trial.getStimulus()[:3]:
            return (1,0,0)
        return (0,0,0)

    # plot regions for image scanpath
    def plotRegions(self, trial):
        frame_color = self.getFrameColor(trial)
        if trial.features['target_side'] == 'Gauche':
            plotRegion(self.left, frame_color)
        elif trial.features['target_side'] == 'Droite':
            plotRegion(self.right, frame_color)
