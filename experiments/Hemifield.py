from eyetracking.experiment import *
from eyetracking.interest_region import *
from PyQt5.QtWidgets import QApplication

class Exp(Experiment):

    def __init__(self):
        super().__init__({"image_end"}, __file__)
        self.n_trials = 120
        self.screen_center = (960,540)
        # Minimal distance at which we consider the subject is looking at the fixation cross at the trial beginning
        self.valid_distance_center = 100

        self.half_width = 235
        self.half_height = 293

        # frames
        self.left = RectangleRegion((self.screen_center[0]/2, self.screen_center[1]), self.half_width, self.half_height)
        self.right = RectangleRegion((self.screen_center[0]*1.5, self.screen_center[1]), self.half_width, self.half_height)


    ###############################################
    ############## Overriden methods ##############
    ###############################################

    # Returns a dictionary of experiment variables
    def parseVariables(self, line: List[str]):
        if len(line) >= 3 and line[2] == "image_end":
            try:
                return {
                    'image_end': int(line[1])
                }
            except:
                pass
        return None

    def parseStartTrial(self, line: List[str]) -> Union[Entry, None]:
        if len(line) >= 3 and line[2] == 'TRIALID':
            try:
                time = int(line[1])
                trial_number = int(line[3].split("/")[0])
                if int(line[3].split("/")[1]) != 8:# training
                    stimulus = line[4]
                    return StartTrial(time, trial_number, stimulus)
            except:
                pass
        return None

    def parseStopTrial(self, line: List[str]) -> Union[Entry, None]:
        if len(line) >= 3 and 'key_pressed' in line[2]:
            try:
                time = int(line[1])
                return StopTrial(time)
            except:
                pass
        return None

    def isResponse(self, line):
        pass

    def isTraining(self, trial):
        return False

    def getTrialRegions(self, trial):
        # WARNING : we don't know where target was
        return [self.left, self.right]

    ######################################################
    ############## End of Overriden methods ##############
    ######################################################

    def processTrial(self, subject: Subject, trial):
        super().processTrial(subject, trial)
        targetName = trial.getStimulus()

        regions = self.getTrialRegions(trial)

        region_fixations = trial.getFixationTime(InterestRegionList(regions))

        # Determining blink category
        if trial.blinks == []:
            blink_category = BLINK.NO
        else:
            if trial.blinks[0].getStartTime() < trial.features["image_end"]:
                blink_category = BLINK.EARLY
            else:
                blink_category = BLINK.LATE

        first_sac_to_target = False
        landing_on_target = False
        if len(trial.saccades) > 0 and len(region_fixations) > 0:
            for saccade in trial.saccades:
                # Saccade must be before first region fixation
                # WARNING : we should select only right or left side depending on side where image was presented
                if saccade.getStartTime() < region_fixations[0].getStartTime():
                    # start of saccade should occur before end of image presentation
                    if saccade.getStartTime() < trial.features["image_end"]:
                        first_sac_to_target = True
                    else:
                        first_sac_to_target = False
            if region_fixations[0].getStartTime() < trial.features["image_end"]:
                landing_on_target = True

        # Error :
        if not trial.isStartValid(self.screen_center, self.valid_distance_center)[0]:
            error = ERROR.START_INVALID
        elif blink_category == BLINK.EARLY:
            error = ERROR.EARLY_BLINK
        elif landing_on_target:
            error = "Landing on target"
        elif first_sac_to_target:
            error = "Saccade toward target"
        elif len(trial.saccades) > 0 and trial.saccades[0].getStartTime() < trial.features["image_end"]:
            error = ERROR.EARLY_SACCADE
        else:
            error = '0'

        # Writing data in result csv file
        new_dict = {
            Col.TARGET: targetName,
            Col.ERR: error,
            Col.BLINK: blink_category,
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
        if image is not None:
            plt.imshow(image)
        for frame in [self.right, self.left]:
            plotRegion(frame, frame_color)
