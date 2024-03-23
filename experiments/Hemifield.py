from eyetracking.experiment import *
from eyetracking.interest_region import *
from PyQt5.QtWidgets import QApplication
import pandas as pd

class HemiCol(Col):
    CORRECTSTART = "Correct start trial"
    SACCADEDURING = "Saccade during face presentation"
    SACCADETOWARD = "Saccade toward face during presentation"
    LANDINGDURING = "Landing on face during presentation"
    AGESTIM = "Age"

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

        self.psychopyVariables = ["StimName", "Emotion", "Age", "StimPos", "Response", "ResponseTime"]


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
                trial_number = int(line[3].split("/")[0])-1 # 1 in Boogui, 0 in psychopy
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
        if trial.features["StimPos"] == 380:
            return [self.right]
        elif trial.features["StimPos"] == -380:
            return [self.left]
        else:
            raise ExperimentException("No valid StimPos {0} for trial {1}".format(trial.features["StimPos"], trial.id))

    ######################################################
    ############## End of Overriden methods ##############
    ######################################################

    # WARNING : hardcoded specifically since we forgot to include side picture was presented in eyelink file
    def getCSVFilePath(self, subject):
        dataPath = "C:/Users/jessi/Ingé/Programmation/Pascal/2023-2024/230927 Tâche eyetracking hémichamp/Données eyetracking/data"
        csvFiles = [file for file in os.listdir(dataPath) if os.path.splitext(file)[1] == ".csv"]
        subjFiles = [file for file in csvFiles if file.startswith("{0}{1}_".format("o" if subject.group == "OLD" else "y", subject.id))]
        if len(subjFiles) != 1:
            raise ExperimentException('{0} files found for subject {1}'.format(len(subjFiles), subject.id))
        return os.path.join(dataPath, subjFiles[0])

    def setCSVVariables(self, subject, trial):
        csvFilePath = self.getCSVFilePath(subject)
        df = pd.read_csv(csvFilePath)
        for row_idx in range(len(df)):
            if df.loc[row_idx, "trials.thisN"] == trial.id:
                for variable in self.psychopyVariables:
                    trial.features[variable] = df.loc[row_idx, variable]

    def processTrial(self, subject: Subject, trial):
        super().processTrial(subject, trial)

        trial_var = self.setCSVVariables(subject, trial)
        regions = self.getTrialRegions(trial)

        region_fixations = trial.getFixationTime(InterestRegionList(regions))

        # Determining blink category
        if trial.blinks == []:
            blink_category = BLINK.NO
        else:
            if trial.blinks[0].getStartTime() < trial.features["image_end"]:
                blink_category = ERROR.EARLY_BLINK
            else:
                blink_category = BLINK.LATE

        sac_to_target = False
        landing_on_target = False
        if len(trial.saccades) > 0 and len(region_fixations) > 0:
            for saccade in trial.saccades:
                # Saccade must be before first region fixation
                if saccade.getStartTime() < region_fixations[0].getStartTime():
                    # start of saccade should occur before end of image presentation
                    if saccade.getStartTime() < trial.features["image_end"]:
                        sac_to_target = True
                    else:
                        sac_to_target = False
            if region_fixations[0].getStartTime() < trial.features["image_end"]:
                landing_on_target = True

        # Writing data in result csv file
        new_dict = {
            Col.TARGET: trial.features["StimName"],
            Col.EMOTION: trial.features["Emotion"],
            HemiCol.AGESTIM: trial.features["Age"],
            Col.TARGET_POS: "Left" if trial.features["StimPos"] == -380 else "Right",
            Col.RESP: trial.features["Response"],
            Col.RT: trial.features['ResponseTime'],
            HemiCol.CORRECTSTART: trial.isStartValid(self.screen_center, self.valid_distance_center)[0],
            HemiCol.SACCADEDURING: len(trial.saccades) > 0 and trial.saccades[0].getStartTime() < trial.features["image_end"],
            HemiCol.SACCADETOWARD: sac_to_target,
            HemiCol.LANDINGDURING: landing_on_target,
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
