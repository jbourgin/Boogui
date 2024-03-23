from eyetracking.experiment import *
from eyetracking.interest_region import *
from eyetracking.plot import *
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication
from matplotlib.offsetbox import OffsetImage

class GCCol(Col):
    # Specific columns
    FIRSTFIX = "First time on eyes"
    TOTAL_EYE = "Total fixation time on eyes"
    TOTAL_FACE = "Total fixation time on face (other than eyes)"
    TOTAL_FIX = "Total fixation time on image (used for percentage computation)"
    PERCENT_EYE = "Percent time on eyes"
    PERCENT_FACE = "Percent time on face"
    FIRST_AREA = "First area looked (1 for eyes)"

class Exp(Experiment):

    def __init__(self):
        super().__init__({'training', 'session', 'global_task', 'emotion', 'gender', 'target_side', 'response', 'cor_resp', 'response_time'}, __file__)
        self.n_trials = 96
        # Center of the screen.
        self.screen_center = (683,384)
        # Minimal distance at which we consider the subject is looking at the
        # fixation cross at the trial beginning
        self.valid_distance_center = 150 #3 degres of visual angle 95 (+ marge)

        # Initializing regions of interest
        self.half_width = 210 #200
        self.half_height_face = 278 #268
        self.half_height_eye = 60 #45 # Increase a little for imprecision

        self.path_images = "D:/Utilisateurs/bourginj/Ingé/ATEMMA/230704 Manip IRMf/images/All"

        # frames
        self.right_gaze = RectangleRegion((self.screen_center[0]*(1+1/3), self.screen_center[1]), self.half_width, self.half_height_eye)
        self.left_gaze = RectangleRegion((self.screen_center[0]-(self.screen_center[0]/3), self.screen_center[1]), self.half_width, self.half_height_eye)
        self.right_ellipse = EllipseRegion((self.screen_center[0]*(1+1/3), self.screen_center[1]), self.half_width, self.half_height_face)
        self.left_ellipse = EllipseRegion((self.screen_center[0]-(self.screen_center[0]/3), self.screen_center[1]), self.half_width, self.half_height_face)
        self.right_face = DifferenceRegion(self.right_ellipse, self.right_gaze)
        self.left_face = DifferenceRegion(self.left_ellipse, self.left_gaze)

        # For postProcess
        self.IVs = [
            Col.EMOTION,
            Col.TASK
        ]

        self.DVs = [
            Col.RT,
            GCCol.TOTAL_FIX
        ]

    ###############################################
    ############## Overriden methods ##############
    ###############################################

    # Returns a dictionary of experiment variables
    def parseVariables(self, line: List[str]):
        if len(line) > 5 and line[2] == "Variable" and line[3] == "values:":
            try:
                if len(line) > 5 and line[2] == "Variable" and line[3] == "values:":
                    training = line[4]
                    session = line[5]
                    global_task = line[6]
                    emotion = line[7]
                    gender = line[8]
                    target_side = line[9]
                    response = line[10]
                    cor_resp = line[11]
                    response_time = line[12]

                return {
                    'training' : training,
                    'session' : session,
                    'global_task' : global_task,
                    'emotion' : emotion,
                    'gender' : gender,
                    'target_side' : target_side,
                    'response' : response,
                    'cor_resp' : cor_resp,
                    'response_time' : response_time
                }
            except:
                pass
        return None

    def isResponse(self, line: Line) -> bool :
        return len(line) >= 5 and 'responded' in line[4]

    def isTraining(self, trial) -> bool:
        return 'Training' in trial.features['training']

    def parseMessage(self, line: List[str]):
        if len(line) > 6 and line[4] == "showing":
            try:
                time = int(line[1])
                message = 'End image showing'
                return Message(time, message)
            except:
                pass
        return None

    def getTrialRegions(self, trial):
        if trial.features['target_side'] == 'Left':
            return [self.left_gaze, self.left_face]
        elif trial.features['target_side'] == 'Right':
            return [self.right_gaze, self.right_face]

    ######################################################
    ############## End of Overriden methods ##############
    ######################################################

    def returnStopImageEntry(self, trial) -> int:
        for count, entry in enumerate(trial.entries):
            if isinstance(entry, Message) and 'End image showing' in entry.message:
                return count
        return None

    def processTrial(self, subject: Subject, trial, filename = None):
        if trial.isEmpty():
            logTrace ("Subject %i has no gaze positions at trial %i !" %(subject.id, trial.id), Precision.DETAIL)
            return
        elif trial.saccades == []:
            logTrace ("Subject %i has no saccades at trial %i !" %(subject.id, trial.id), Precision.DETAIL)
            return

        # Do processTrial of parent after making sure that the trial will be considered
        super().processTrial(subject, trial)
        start_trial_time = trial.getStartTrial().getTime()

        first_saccade = trial.saccades[0].getStartTimeFromStartTrial()

        if trial.features['target_side'] == 'Left':
            start_point = (self.screen_center[0]*(1+1/3), self.screen_center[1]+150)
        elif trial.features['target_side'] == 'Right':
            start_point = (self.screen_center[0]-(self.screen_center[0]/3), self.screen_center[1]+150)
        regions = self.getTrialRegions(trial)
        eye_position = regions[0]
        face_position = regions[1]

        end_line = self.returnStopImageEntry(trial)

        response_entry = trial.getResponse()

        region_fixations = trial.getFixationTime(InterestRegionList(regions), eye_position, end_line)

        # First and last good fixations
        try:
            # Fixations on eye region
            first_fixation = next(fixation for fixation in region_fixations)
            if first_fixation.on_target:
                first_area = 1
            else:
                first_area = 0
        except:
            first_fixation = None
            first_area = None
        try:
            first_good_fixation = next(fixation for fixation in region_fixations if fixation.on_target)
            capture_delay_first = first_good_fixation.getStartTimeFromStartTrial()
        except:
            first_good_fixation = None
            capture_delay_first = None

        # Time on target and distractors
        total_eye_fixation_time = sum(x.duration() for x in region_fixations if x.on_target)
        total_faceNotEye_fixation_time = sum(x.duration() for x in region_fixations if not x.on_target)
        total_fixation_time = total_eye_fixation_time + total_faceNotEye_fixation_time
        if total_fixation_time != 0:
            percent_eye = total_eye_fixation_time/total_fixation_time*100
            percent_face = total_faceNotEye_fixation_time/total_fixation_time*100
        else:
            percent_eye = None
            percent_face = None

        # Determining blink category
        if trial.blinks == []:
            blink_category = BLINK.NO
        else:
            if region_fixations != []:
                if trial.blinks[0].getStartTime() < region_fixations[0].getStartTime():
                    blink_category = BLINK.EARLY
                else:
                    blink_category = BLINK.LATE
            else:
                blink_category = None

        # Error :

        if not trial.isStartValid(start_point, self.valid_distance_center)[0]:
             error = ERROR.START_INVALID
        elif trial.features['response'] == 'None':
            error = ERROR.NO_RESPONSE
        elif total_fixation_time < 2000:
            error = ERROR.SHORT_FIXATION
        elif blink_category == BLINK.EARLY:
            error = ERROR.EARLY_BLINK
        elif first_fixation is None:
            error = ERROR.NO_FIXATION
        elif first_saccade < 50:
            error = ERROR.EARLY_SACCADE
        else:
            if trial.features['cor_resp'] != trial.features['response']:
                error = 1
            else:
                error = 0

        # Compiling data in trial_dict
        new_dict = {
            Col.TRAINING: trial.isTraining(),
            Col.SESSION: trial.features['session'],
            Col.TASK: trial.features['global_task'],
            Col.EMOTION: trial.features['emotion'],
            Col.GENDER: trial.features['gender'],
            Col.TARGET: trial.getStimulus().split('.')[0],
            Col.TARGET_POS: trial.features['target_side'],
            Col.COR_RESP: trial.features['cor_resp'],
            Col.RESP: trial.features['response'],
            Col.ERR: error,
            Col.RT: trial.features['response_time'],
            GCCol.FIRSTFIX: capture_delay_first,
            GCCol.TOTAL_EYE: total_eye_fixation_time,
            GCCol.TOTAL_FACE: total_faceNotEye_fixation_time,
            GCCol.TOTAL_FIX: total_fixation_time,
            GCCol.PERCENT_EYE: percent_eye,
            GCCol.PERCENT_FACE: percent_face,
            Col.BLINK: blink_category,
            GCCol.FIRST_AREA: first_area
        }

        self.updateDict(new_dict)

    def isEligibleTrial(self, trial, DV):
        return super().isEligibleTrial(trial, DV) and trial[DV] != "None" and (trial[Col.ERR] == "0" or trial[Col.ERR] == 0)


    ######################################################
    ###################### Plot data #####################
    ######################################################

    # plot regions for image plot
    def plotRegions(self, trial, image):
        frame_color = self.getFrameColor(trial)
        img_width = self.half_width
        img_height = self.half_height_face

        # Plotting frames
        if trial.features['target_side'] == 'Left':
            if image is not None:
                plt.imshow(image, extent=[
                    self.left_ellipse.center[0] - img_width,
                    self.left_ellipse.center[0] + img_width,
                    self.left_ellipse.center[1] + img_height,
                    self.left_ellipse.center[1] - img_height
                ])
            plotRegion(self.left_ellipse, frame_color)
            plotRegion(self.left_gaze, frame_color)
        elif trial.features['target_side'] == 'Right':
            if image is not None:
                plt.imshow(image, extent=[
                    self.right_ellipse.center[0] - img_width,
                    self.right_ellipse.center[0] + img_width,
                    self.right_ellipse.center[1] + img_height,
                    self.right_ellipse.center[1] - img_height
                ])
            plotRegion(self.right_ellipse, frame_color)
            plotRegion(self.right_gaze, frame_color)
