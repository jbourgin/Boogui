import re #To format data lists
from eyetracking.experiment import *
from eyetracking.interest_region import *
from PyQt5.QtWidgets import QApplication
from enum import Enum

class EDCol(Col):

    # Specific columns
    TRIALTYPE = "Type essai"
    STIMTYPE = "Type stimulus"
    STIMEMO = "Stimulus emo"
    STIMNEU = "Stimulus neu"
    FRAME = "Forme"
    FIRSTFIX = "First fixation"
    FAILED = "Failed eyetracking" # if recalibration took place during trial (should be discarded)

class StimType(Enum):
    SCENE = "Scene"
    FACE = "Face"

class TrialType(Enum):
    CONTROL = "Control"
    ENGAGEMENT = "Engagement"
    DISENGAGEMENT = "Disengagement"

class Exp(Experiment):

    def __init__(self):
        super().__init__({'start_wait_sac', 'frame', 'pos_frame', 'correct', 'trialType', 'failed_trial', 'stim_emo', 'stim_neu', 'emotion', 'response_time'}, __file__)
        self.n_trials = 48

        #Center of the screen
        self.screen_center = (960, 540)

        self.valid_distance_center = 95

        self.half_height = {}
        self.half_width = {}
        self.half_height[StimType.FACE] = 180
        self.half_width[StimType.FACE] = 140
        self.half_height[StimType.SCENE] = 150
        self.half_width[StimType.SCENE] = 200

        self.frame_list = {}
        for stimType in StimType:
            self.frame_list[stimType] = {}
            self.frame_list[stimType]["-440"] = RectangleRegion((self.screen_center[0]-440, self.screen_center[1]), self.half_width[stimType], self.half_height[stimType])
            self.frame_list[stimType]["440"]= RectangleRegion((self.screen_center[0]+440, self.screen_center[1]), self.half_width[stimType], self.half_height[stimType])

        # For postProcess
        self.IVs = [
            Col.EMOTION,
            EDCol.TRIALTYPE
        ]

        self.DVs = [
            EDCol.FIRSTFIX,
            Col.RT
        ]

    ###############################################
    ############## Overriden methods ##############
    ###############################################

    # Returns a dictionary of experiment variables
    def parseVariables(self, line: List[str]):
        if len(line) >= 4 and line[2] == "start_wait_sac":
            return {
                "start_wait_sac": line[1]
            }
        elif any(f in line for f in self.expected_features):
            parseDict = {}
            for f in self.expected_features:
                if f in line:
                    parseDict[f] = line[line.index(f)+1]
            return parseDict
        return None

    def isResponse(self, line: Line) -> bool :
        return len(line) > 4 and 'cor_response' in line[4]

    def isTraining(self, trial) -> bool:
        return any(s in trial.features["stim_emo"] for s in ["training", "Training"])

    def parseSubject(self, input_file : str, progress = None) -> Subject:
        datafile = open(input_file, 'r')

        #File conversion in list.
        data = datafile.read()
        data = list(data.splitlines())

        #We add a tabulation and space separator.
        data = [re.split('[\t ]+',line) for line in data]

        n_subject = int(os.path.basename(os.path.splitext(input_file)[0]).split("_")[1])

        return Subject(self, self.n_trials, data, n_subject, None, progress)

    def getTrialRegions(self, trial):
        return [self.frame_list[trial.features["stimType"]][trial.features["pos_frame"]]]

    ######################################################
    ############## End of Overriden methods ##############
    ######################################################

    def processTrial(self, subject: Subject, trial):

        if trial.saccades == []:
            logTrace ('Subject %i has no saccades at trial %i !' %(subject.id, trial.id), Precision.DETAIL)
            return
        elif trial.features["trialType"] == TrialType.CONTROL.value:
            logTrace ('Skip Control trial %i for subject %i' %(trial.id, subject.id), Precision.DETAIL)
            return
        elif trial.features["failed_trial"] == "1":
            logTrace ('Had to recalibrate during trial %i for subject %i' %(trial.id, subject.id), Precision.DETAIL)
            return
        else:
            if any(f in trial.features["stim_emo"] for f in ["Homme", "Femme"]):
                trial.features["stimType"] = StimType.FACE
            else:
                trial.features["stimType"] = StimType.SCENE
        # Do processTrial of parent after making sure that the trial will be considered
        super().processTrial(subject, trial)
        target = self.getTrialRegions(trial)[0]

        # Get all fixations that occurred on target only after wait for saccade toward frame begins
        region_fixations = [x for x in trial.getFixationTime(InterestRegionList([target]), target) if x.getStartTime() > int(trial.features["start_wait_sac"])]

        # Get all saccades tat occurred after wait for saccade toward frame begins
        saccades = [x for x in trial.saccades if x.getStartTime() > int(trial.features["start_wait_sac"])]

        # Get first fixation on target after wait for sac starts
        first_fixation = None
        if len(region_fixations) != 0:
            first_fixation = next(iter(region_fixations))


        # Determining blink category
        if trial.blinks == []:
            blink_category = BLINK.NO
        else:
            blink_category = BLINK.LATE
            if first_fixation is not None:
                for blink in trial.blinks:
                    if int(trial.features["start_wait_sac"]) < blink.getStartTime() < first_fixation.getStartTime():
                        blink_category = BLINK.EARLY
                        break
            else:
                blink_category = None

        # Error :
        if not trial.isStartValid(self.screen_center, self.valid_distance_center)[0]:
            error = ERROR.START_INVALID
        elif blink_category == BLINK.EARLY:
            error = ERROR.EARLY_BLINK
        elif first_fixation is None:
            error = ERROR.NO_FIXATION
        elif len(saccades) > 0 and saccades[0].getStartTime() - int(trial.features["start_wait_sac"]) < 60:
            error = ERROR.EARLY_SACCADE
        else: # 1 if subject gave wrong manual answer
            error = 0 if trial.features["correct"] == "1" else 1

        # Compiling data in trial_dict
        new_dict = {
            Col.TRAINING: trial.isTraining(),
            EDCol.TRIALTYPE: trial.features["trialType"],
            EDCol.STIMTYPE: trial.features["stimType"].value,
            Col.EMOTION: trial.features["emotion"],
            EDCol.STIMEMO: trial.features["stim_emo"],
            EDCol.STIMNEU: trial.features["stim_neu"],
            EDCol.FRAME: trial.features["frame"],
            Col.TARGET_POS: "Right" if trial.features["pos_frame"] == "440" else "Left",
            EDCol.FIRSTFIX: None if first_fixation is None else first_fixation.getStartTime() - int(trial.features["start_wait_sac"]),
            Col.ERR: error,
            Col.RT: trial.features["response_time"],
            EDCol.FAILED: trial.features["failed_trial"],
            Col.BLINK: blink_category
        }

        self.updateDict(new_dict)

    def isEligibleTrial(self, trial, DV):
        if DV in [EDCol.FIRSTFIX, EDCol.RT]:
            # Exclude trials with no saccade and trials with error or non desired events (blink, anticipation, etc.)
            return super().isEligibleTrial(trial, DV) and trial[EDCol.FIRSTFIX] != None and (trial[EDCol.ERR] == "0" or trial[EDCol.ERR] == 0)
        return True

    ######################################################
    ###################### Plot data #####################
    ######################################################

    # Get frame color (stim delimitation during plot)
    def getFrameColor(self, trial):
        if trial.features["trialType"] == TrialType.DISENGAGEMENT.value:
            return (0,1,0)
        else:
            return (1,0,0)

    # plot regions for image plot
    def plotRegions(self, trial, image):
        frame_color = self.getFrameColor(trial)
        if trial.features["trialType"] != TrialType.CONTROL.value:
            # Plotting frames
            plotRegion(self.frame_list[StimType.SCENE][trial.features["pos_frame"]], frame_color)

            other_frame = "440" if trial.features["pos_frame"] == "-440" else "-440"
            plotRegion(self.frame_list[StimType.SCENE][other_frame], (0,0,0))
