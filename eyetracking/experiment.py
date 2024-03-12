import attr
import re #To format data lists
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
from typing import List, Dict, Union, Set

from eyetracking.utils import *
from eyetracking.subject import *
from eyetracking.entry import *
from eyetracking.plot import *
import itertools

class Col():

    # Columns constants
    SUBJID = "Subject"
    GROUP = "Group"
    TRIALID = "TrialID"
    EYE = "Eye"
    BLINK = "First blink type"
    TRAINING = "Training"
    TASK = "Task"
    SESSION = "Session"
    EMOTION = "Emotion"
    GENDER = "Gender"
    TARGET = "Target Name"
    TARGET_POS = "Target Position"
    RESP = "Subject response"
    COR_RESP = "Correct response"
    ERR = "Errors"
    RT = "Response time"

class ERROR():

    # Error type constants
    START_INVALID = "No valid start"
    EARLY_BLINK = "Early blink"
    SHORT_SACCADE = "Short saccade"
    EARLY_SACCADE = "Anticipation saccade"
    MICRO_SACCADE = "Micro saccade"
    NO_FIXATION = "No fixation"
    SHORT_FIXATION = "Low fixation time"
    NO_RESPONSE = "No response"

class PROCESS():
    MEAN = "Mean"
    SD = "SD"
    SORTING = "sorting"

class BLINK():
    NO = "No blink"
    EARLY = "Early capture"
    LATE = "Late"

class ExperimentException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

class Experiment (ABC):

    plotMethod = PlotMethod.FIX
    frequency = 10 # We draw 10 points/sec (one each 100 ms)

    def __init__(self, expected_features: Set[str], exp_name):
        self.expected_features = expected_features
        self.dataframe = None
        self.trial_dict = dict()
        self.exp_name = os.path.basename(os.path.splitext(exp_name)[0])
        self.path_images = None
        self.IVs = []
        self.DVs = []

    def processSubject(self, input_file: str, progress_bar = None) -> "Subject":
        subject = self.parseSubject(input_file, progress_bar)
        if self.isSubjectValid(subject):
            return subject
        else:
            raise ExperimentException('File %s does not fit the experiment' % input_file)

    # Returns true if this subject made this experiment
    def isSubjectValid(self, subject : "Subject") -> bool:
        if len(subject.trials) == 0:
            logTrace('Subject has no trial', Precision.ERROR)
            return False
        if self.expected_features == set():
            logTrace('Experiment has no expected features', Precision.ERROR)
            return False
        for trial in subject.trials:
            features = trial.features.keys()
            if self.expected_features == features:
                return True
        # If no trial has expected features
        logTrace('Expected features %s, got %s for trial 0' % (self.expected_features, features), Precision.ERROR)
        return False

    @staticmethod
    def getEye(lines: List[List[str]]) -> str:
        for line in lines:
            if len(line) > 2 and line[0] == "SSACC":
                return line[1]
        return None

    # WARNING : we assume that record freq will not change for a given subject throughout the experiment.
    @staticmethod
    def getRecordFreq(lines: List[List[str]]) -> float:
        for line in lines:
            if len(line) >= 5 and line[0] == "EVENTS" and line[3] == "RATE":
                return float(line[4])
        return None

    @staticmethod
    def getPlotStep(recordFreq):
        return int(recordFreq/Experiment.frequency)

    #######################################
    ############ ENTRY PARSERS ############
    #######################################
    # Each of the following parser tries to parse one type of Entry
    # If is fails, it returns None

    def parseStartTrial(self, line: List[str]) -> Union[Entry, None]:
        if len(line) >= 5 and line[2] == 'start_trial':
            try:
                time = int(line[1])
                trial_number = int(line[3])
                stimulus = ''.join(line[4:])
                return StartTrial(time, trial_number, stimulus)
            except:
                pass
        return None

    def parseStopTrial(self, line: List[str]) -> Union[Entry, None]:
        if len(line) >= 3 and line[2] == 'stop_trial':
            try:
                time = int(line[1])
                return StopTrial(time)
            except:
                pass
        return None

    def parsePosition(self, line: List[str]) -> Union[Entry, None]:
        # case Position
        if len(line) >= 3:
            try:
                time = int(line[0])
                x = float(line[1])
                y = float(line[2])
                return Position(time, x, y)
            except:
                pass
        return None

    def parseStartFixation(self, line: List[str]) -> Union[Entry, None]:
        # case Position
        if len(line) >= 3 and line[0] == 'SFIX':
            try:
                time = int(line[2])
                return StartFixation(time)
            except:
                pass
        return None

    def parseEndFixation(self, line: List[str]) -> Union[Entry, None]:
        # case Position
        if len(line) >= 4 and line[0] == 'EFIX':
            try:
                time = int(line[3])
                return EndFixation(time)
            except:
                pass
        return None

    def parseStartBlink(self, line: List[str]) -> Union[Entry, None]:
        # case Position
        if len(line) >= 3 and line[0] == 'SBLINK':
            try:
                time = int(line[2])
                return StartBlink(time)
            except:
                pass
        return None

    def parseEndBlink(self, line: List[str]) -> Union[Entry, None]:
        # case Position
        if len(line) >= 4 and line[0] == 'EBLINK':
            try:
                time = int(line[3])
                return EndBlink(time)
            except:
                pass
        return None

    def parseStartSaccade(self, line: List[str]) -> Union[Entry, None]:
        # case Position
        if len(line) >= 3 and line[0] == 'SSACC':
            try:
                time = int(line[2])
                return StartSaccade(time)
            except:
                pass
        return None

    def parseEndSaccade(self, line: List[str]) -> Union[Entry, None]:
        # case Position
        if len(line) >= 4 and line[0] == 'ESACC':
            try:
                time = int(line[3])
                return EndSaccade(time)
            except:
                pass
        return None

    def parseResponse(self, line: Line) -> Union[Entry, None]:
        # case Position
        if self.isResponse(line):
            try:
                time = int(line[1])
                return Response(time)
            except:
                pass
        return None

    def parseExperimentVariables(self, line: List[str]) -> Union[Entry, None]:
        # case Position
        try:
            time = int(line[1])
            variables = self.parseVariables(line)
            if variables != None:
                return TrialFeatures(time, variables)
            else:
                return None
        except:
            return None

    def parseMessage(self, line: Line) -> Union[Entry, None]:
        try:
            time = int(line[1])
            message = ' '.join(line[2:])
            return Message(time, message)
        except:
            return None


    def parseEntry(self, line: List[str]) -> Union[Entry, None]:
        parsers = [self.parseStartTrial,
            self.parseStopTrial,
            self.parsePosition,
            self.parseStartFixation,
            self.parseEndFixation,
            self.parseStartBlink,
            self.parseEndBlink,
            self.parseStartSaccade,
            self.parseEndSaccade,
            self.parseResponse,
            self.parseExperimentVariables,
            self.parseMessage]

        for parser in parsers:
            res = parser(line)
            if res != None:
                return res

        return None

    def getSubjectData(self, line: str) -> Union[Tuple[int,str]]:
        try:
            l = re.split('[\t ]+', line)
            return (int(l[1]), l[2])
        except:
            return None

    def parseSubject(self, input_file : str, progress = None) -> Subject:

        with open(input_file) as f:
            first_line = f.readline()
            if first_line[-1] == '\n':
                first_line = first_line[:-1]

        subject_data = self.getSubjectData(first_line)

        if subject_data is None:
            raise ExperimentException('Subject number and category could not be found')

        else:
            result_file = 'results.txt'
            datafile = open(input_file, 'r')

            #File conversion in list.
            data = datafile.read()
            data = list(data.splitlines())

            #We add a tabulation and space separator.
            data = [re.split('[\t ]+',line) for line in data]

            (n_subject, subject_cat) = subject_data
            return Subject(self, self.n_trials, data, n_subject, subject_cat, progress)

    #######################################
    ############ Trial process ############
    #######################################
    @abstractmethod
    def getTrialRegions(self, trial) -> List:
        pass

    def processTrial(self, subject : "Subject", trial : Trial) -> None:
        logTrace ('Processing trial n°%i' % trial.id, Precision.DETAIL)

        new_dict = {
            Col.SUBJID: "%i"%subject.id,
            Col.GROUP: subject.group,
            Col.TRIALID: trial.id,
            Col.EYE: trial.eye,
        }

        self.updateDict(new_dict)

    def updateDict(self, new_dict) -> None:
        updateListDict(self.trial_dict, new_dict)

    # isEligibleTrial for filtering outliers
    def isEligibleTrial(self, trial, DV) -> bool:
        # Check that DV value is number
        return isinstance(trial[DV], int) or isinstance(trial[DV], float) or (isinstance(trial[DV], str) and isFloat(trial[DV]))

    def postProcess(self) -> None:
        # No post process if no DV provided
        if len(self.DVs) == 0:
            logTrace('No DV provided for experiment %s : post process halted'%self.exp_name, Precision.NORMAL)
            return

        # Create all IV combinations (e.g., (Pos, 3), (Pos, 5), (Neg, 3), (Neg, 5))
        IV_list = [[IVVal for IVVal in self.dataframe[IVCol].unique()] for IVCol in self.IVs]
        IV_combinations = [p for p in itertools.product(*IV_list)]

        # Init sorting columns
        for DV in self.DVs:
            self.dataframe['{0}_{1}'.format(DV, PROCESS.SORTING)] = ""

        # For each subject
        for subjID in self.dataframe[Col.SUBJID].unique():
            subj_df = self.dataframe.loc[self.dataframe[Col.SUBJID] == subjID]

            for IV_combination in IV_combinations:
                # Successively filter for each IVVal (e.g., only negative trials, then only trials with 5 distractors, etc.)
                combination_df = subj_df
                for count, IVVal in enumerate(IV_combination):
                    combination_df = combination_df.loc[combination_df[self.IVs[count]] == IVVal]
                # For each dependent variable
                for DV in self.DVs:
                    # Dict to hold mean and SD for current DV
                    IV_df = nested_dict()
                    # Keep only eligible trials
                    DV_df = [float(x[DV]) for x in combination_df.to_dict(orient='records') if self.isEligibleTrial(x, DV)]
                    # Compute mean and standard deviation (nan versions ignore NaN)
                    IV_df[IV_combination][PROCESS.MEAN] = np.nanmean(DV_df)
                    IV_df[IV_combination][PROCESS.SD] = np.nanstd(DV_df)
                    for row_num, row in combination_df.iterrows():
                        # Default : normal
                        row_status = "Normal {0} value".format(DV)
                        if self.isEligibleTrial(row.to_dict(), DV):
                            # Reverse order : 2 then 3. We need to do this in this order, since a value deviant by 3SDs will also be deviant by 2 (we would have no 3SDs deviant if we did it in decremental order)
                            for nbSD in [2,3]:
                                # Outlier
                                if isOutlier(row[DV], IV_df[IV_combination][PROCESS.MEAN], IV_df[IV_combination][PROCESS.SD], nbSD):
                                    row_status = "Deviant {0} {1} SD".format(DV, nbSD)
                                    logTrace("{0} in a {1} trial exceeds {2} SD for subject {3} : {4}, mean: {5}, SD: {6}".format(DV, "-".join(IV_combination), nbSD, subjID, row[DV], IV_df[IV_combination][PROCESS.MEAN], IV_df[IV_combination][PROCESS.SD]), Precision.NORMAL)
                        # Not eligible
                        else:
                            row_status = "{0} not relevant".format(DV)
                        combination_df.at[row_num, '{0}_{1}'.format(DV, PROCESS.SORTING)] = row_status
                # Put updated filtered df back to main self.dataframe
                self.dataframe.loc[combination_df.index] = combination_df


    #######################################
    ############# Data plot ###############
    #######################################

    # Draw base plot : create image with correct dimensions and plot images and regions (shared by video and image plot)
    def drawBasePlot(self, trial):
        plt.clf()

        x_axis = self.screen_center[0] * 2
        y_axis = self.screen_center[1] * 2
        plt.axis([0, x_axis, 0, y_axis])
        plt.gca().invert_yaxis()
        plt.axis('off')

        # Plotting image
        # Valid if only one image to show
        image = None
        if self.path_images is not None:
            image_name = os.path.join(
                self.path_images,
                trial.getStimulus().split('.')[0] + '.png'
            )
            if os.path.isfile(image_name):
                image = plt.imread(image_name, format = 'png')

        # depends on experiment
        self.plotRegions(trial, image)

    def getPlotName(self, trial, subject, extension):
        return 'exp_%s_subject_%s%i_%s_%i_%s.%s' % (self.exp_name, subject.group, subject.id, "training" if trial.isTraining() else "trial", trial.id, Experiment.plotMethod.value.lower(), extension)

    # Get frame color (stim delimitation during plot)
    def getFrameColor(self, trial):
        return (0,0,0)

    # Creates an image plot for one trial.
    def plot(self, subject: Subject, trial) -> str:
        self.drawBasePlot(trial)

        # For GazeContingent only
        try: end_line = self.returnStopImageEntry(trial)
        except AttributeError: end_line = None
        # Plotting gaze positions
        trial.plot(self.getPlotStep(subject.recordFreq), end_line)
        image_name = self.savePlot(trial, subject)
        return image_name

    def savePlot(self, trial, subject) -> str:
    	image_name = self.getPlotName(trial, subject, "png")
    	saveImage(getPlotsFolder(), image_name)
    	return image_name

    # Creates a video scanpath for one trial.
    def scanpathVideo(self, subject : "Subject", trial : Trial, progress = None) -> str:
        n_elem_drawn = 20
        point_list = trial.getGazePoints()
        nb_points = len(point_list)
        point_color = (1,1,0)

        plotStep = self.getPlotStep(subject.recordFreq)
        # Taking frequency into account
        point_list_f = []
        for i in range(0,len(point_list)-plotStep,plotStep):
            point_list_f.append(point_list[i])

        image_list = []

        logTrace ('Creating video frames', Precision.NORMAL)

        if progress != None:
            progress.setText(0, 'Loading frames')
            progress.setMaximum(0, len(point_list_f) - 1)

        for elem in range(0,len(point_list_f)-1):
            if progress != None:
                progress.increment(0)
            self.drawBasePlot(trial)

            for j in range(max(0,elem-n_elem_drawn),elem+1):
                plotSegment(point_list_f[j], point_list_f[j+1], c = point_color)
            point_color = (1, point_color[1] - 1.0/nb_points , 0)

            image_name = '%i.png' % elem
            saveImage(getTmpFolder(), image_name)
            image_list.append(joinPaths(getTmpFolder(), image_name))

        vid_name = self.getPlotName(trial, subject, "avi")

        progress.setText(0, 'Loading frames')
        # TODO : update fps
        makeVideo(image_list, vid_name, fps=Experiment.frequency)
        return vid_name

    ##########################################
    ############ Abstract methods ############
    ##########################################
    @abstractmethod
    def isResponse(self, line : Line) -> bool:
        pass

    @abstractmethod
    def isTraining(self, trial) -> bool:
        pass

    @abstractmethod
    def parseVariables(self, line: Line):
        """
        Returns a dictionary of experiment variables
        """
        pass

    @abstractmethod
    def plotRegions(self, trial):
        pass
