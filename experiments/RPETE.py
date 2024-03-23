from eyetracking.experiment import *
from eyetracking.interest_region import *
from PyQt5.QtWidgets import QApplication

class RPETECol(Col):

    # Specific columns
    SEMANTIC = "Semantic relation"
    TOTAL_FIX = "Total fixation time on ROIs"
    AVG_FIX = "Average fixation duration on ROIs"
    NB_SACCADES = "Total number of saccades"
    NB_REVISITS = "Total number of revisits"

class SemanticRelation(Enum):
    CONTROL = "Control"
    FUNCTIONAL = "Functional"
    COLLATERAL = "Collateral"

class Exp(Experiment):

    def parseStim(self, stimName):
        return stimName.replace("stim/","").replace(".png","")

    def __init__(self):
        super().__init__({"image_onset"}, __file__)
        self.n_trials = 18
        self.screen_center = (960,540)
        # Minimal distance at which we consider the subject is looking at the fixation cross at the trial beginning
        self.valid_distance_center = 100

        # WARNING : Hard path
        self.path_images = "C:\\Users\\jessi\\Ingé\\Programmation\\Anne L\\2023-2024\\Eyetracking Mélanie\\RPETE\\stim"

        # frames
        self.frames = {}
        self.correct_responses = {}
        # WARNING : We get frames in CSV file, which needs to be in Boogui data folder
        df = pd.read_excel("data\\RPETE\\stim_psychopy.xlsx")
        # TODO : widen a little bit regions since some of them are really small ?
        for row_num in range(len(df)):
            stimName = self.parseStim(df.loc[row_num, "StimName"])
            self.frames[stimName] = []
            for word_num in range(1,8):
                word = df.loc[row_num, "word%i"%word_num]
                if not pd.isnull(word) and word not in ["plus", "moins"]: # We exclude operation terms
                    splitted_size = df.loc[row_num, "size%i"%word_num].split(",")
                    width = splitted_size[0].replace("(","")
                    height = splitted_size[1].replace(")","")
                    splitted_pos = df.loc[row_num, "pos%i"%word_num].split(",")
                    pos_h = float(splitted_pos[0].replace("(","")) + self.screen_center[0]
                    pos_v = -float(splitted_pos[1].replace(")", "")) + self.screen_center[1]

                    word_dict = {"word": word, "half_width": int(width)/2, "half_height": int(height)/2, "pos": (float(pos_h), float(pos_v))}
                    self.frames[stimName].append(word_dict)

            self.correct_responses[stimName] = df.loc[row_num, "ExpectedResponse"]

        self.sem_info = {}
        self.sem_info.update({str(i):SemanticRelation.COLLATERAL for i in [1, 2, 3, 4, 13, 14]})
        self.sem_info.update({str(i):SemanticRelation.FUNCTIONAL for i in [5, 6, 7, 8, 15, 16]})
        self.sem_info.update({str(i):SemanticRelation.CONTROL for i in [9, 10, 11, 12, 17, 18]})

        # For postProcess
        # self.IVs = [
        #     RPETECol.SEMANTIC
        # ]
        #
        # self.DVs = [
        #     Col.RT,
        #     RPETECol.TOTAL_FIX,
        #     RPETECol.AVG_FIX,
        #     RPETECol.NB_SACCADES,
        #     RPETECol.NB_REVISITS
        # ]


    ###############################################
    ############## Overriden methods ##############
    ###############################################

    # Returns a dictionary of experiment variables
    def parseVariables(self, line: List[str]):
        if len(line) >= 3 and line[2] == 'image_onset':
            try:
                return {
                    'image_onset': int(line[1])
                }
            except:
                pass
        return None

    def parseStartTrial(self, line: List[str]) -> Union[Entry, None]:
        if len(line) >= 5 and line[2] == 'TRIALID':
            try:
                time = int(line[1])
                trial_number = int(line[3].split("/")[0])
                stimulus = self.parseStim(line[4])

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
        rectangleRegions = []
        for frame in self.frames[trial.getStimulus()]:
            rectangleRegions.append(self.getRegion(frame))

        return rectangleRegions

    ######################################################
    ############## End of Overriden methods ##############
    ######################################################

    def getRegion(self, frame):
        return RectangleRegion(frame["pos"], frame["half_width"], frame["half_height"])

    def processTrial(self, subject: Subject, trial):
        if trial.isEmpty():
            logTrace ("Subject %i has no gaze positions at trial %i !" %(subject.id, trial.id), Precision.DETAIL)
            return
        super().processTrial(subject, trial)
        targetName = trial.getStimulus()

        fix_cross_pos = (100,100)

        if trial.saccades == []:
            logTrace ('Subject %i has no saccades at trial %i !' %(subject.id, trial.id), Precision.DETAIL)
            return

        regions = self.getTrialRegions(trial)

        region_fixations = trial.getFixationTime(InterestRegionList(regions))

        # VDs
        response_time = trial.getStopTrial().getTime() - trial.features["image_onset"]
        total_fix_time = sum(x.duration() for x in region_fixations)
        avg_fix_time = 0
        if len(region_fixations) != 0:
            avg_fix_time = total_fix_time/len(region_fixations)

        # WARNING : the total nb revisits is the sum of all revisits on any given ROIs. First visit is not counted.
        visited_regions = []
        total_nb_revisits = 0
        for fix in region_fixations:
            if fix.region not in visited_regions:
                visited_regions.append(fix.region)
            else:
                total_nb_revisits += 1

        # Determining blink category
        if trial.blinks == []:
            blink_category = BLINK.NO
        else:
            if trial.blinks[0].getStartTime() < trial.saccades[0].getStartTime():
                blink_category = BLINK.EARLY
            else:
                blink_category = BLINK.LATE

        # Error :
        if not trial.isStartValid(fix_cross_pos, self.valid_distance_center)[0]:
            error = ERROR.START_INVALID
        elif blink_category == BLINK.EARLY:
            error = ERROR.EARLY_BLINK
        elif trial.saccades[0].getStartTime() - trial.features["image_onset"] < 50:
            error = ERROR.EARLY_SACCADE
        elif len(region_fixations) == 0:
            error = ERROR.NO_FIXATION
        else:
            error = '0'

        # Writing data in result csv file
        new_dict = {
            RPETECol.SEMANTIC: self.sem_info[targetName].value,
            Col.TARGET: targetName,
            Col.COR_RESP: self.correct_responses[targetName],
            Col.ERR: error,
            Col.RT: response_time,
            RPETECol.TOTAL_FIX: total_fix_time,
            RPETECol.AVG_FIX: avg_fix_time,
            RPETECol.NB_SACCADES: len(trial.saccades),
            RPETECol.NB_REVISITS: total_nb_revisits,
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
        for frame in self.frames[trial.getStimulus()]:
            plotRegion(self.getRegion(frame), frame_color)
