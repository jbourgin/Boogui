import re #To format data lists
from eyetracking.eyelink import *
from eyetracking.smi import *
from eyetracking.experiment import *
from eyetracking.interest_region import *
from eyetracking.scanpath import *
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication

class Make_Eyelink(Eyelink):
    def __init__(self):
        super().__init__()
        # Center of the screen.
        self.screen_center = (512,384)
        # Minimal distance at which we consider the subject is looking at the
        # fixation cross at the trial beginning
        self.valid_distance_center = 90 #3 degres of visual angle 95 (+ marge)

        # Initializing regions of interest
        self.half_width = 128
        self.half_height = 128

        # frames
        self.right = RectangleRegion((self.screen_center[0]*1.5, self.screen_center[1]), self.half_width, self.half_height)
        self.left = RectangleRegion((self.screen_center[0]/2, self.screen_center[1]), self.half_width, self.half_height)

    # Returns a dictionary of experiment variables
    def parseVariables(self, line: List[str]):
        if len(line) > 5 and line[3] == "stim1":
            try:
                stim1 = line[5]
                stim2 = line[10]
                arrow = line[15]
                emotion = line[20]

            except:
                pass
        elif len(line) > 5 and line[3] == "target_side":
            try:
                target_side = line[5]
                position_emo = line[10]
                position_neu = line[15]

                return {
                    'stim1' : stim1,
                    'stim2' : stim2,
                    'arrow' : arrow,
                    'emotion' : emotion,
                    'target_side' : target_side,
                    'position_emo' : position_emo,
                    'position_neu' : position_neu,
                    }

            except:
                pass
        return None

    def isResponse(self, line: Line) -> bool :
        logTrace ('Stop_trial for response line ok?', Precision.TITLE)
        return len(line) >= 2 and 'stop_trial' in line[2]

    def isTraining(self, trial) -> bool:
        return 'Dis' in trial.features['stim1']

class Prosaccade(Experiment):

    def __init__(self):
        super().__init__(None)
        logTrace ('Number of trials to change', Precision.TITLE)
        self.n_trials = 9 #80

    def selectEyetracker(self, input_file : str) -> None:
        logTrace ('Selecting Eyelink', Precision.NORMAL)
        self.eyetracker = Make_Eyelink()

    def processTrial(self, subject, trial, filename = None):
        logTrace ('Processing trial n°%i' % trial.getTrialId(), Precision.DETAIL)
        trial_number = trial.getTrialId()

        if trial.saccades == []:
            logTrace ("Subject %i has no saccades at trial %i !" %(subject.id,trial_number), Precision.DETAIL)

        if trial.features['position_emo'] == '-300':
            emo_position = self.eyetracker.left
            neu_position = self.eyetracker.right
        elif trial.features['position_emo'] == '300':
            emo_position = self.eyetracker.right
            neu_position = self.eyetracker.left
        regions = InterestRegionList([emo_position, neu_position])

        start_trial_time = trial.getStartTrial().getTime()

        targetname = trial.features['stim1']

        response_entry = trial.getResponse()

        region_fixations = trial.getFixationTime(regions, emo_position)

        # First fixations
        try:
            first_fixation = next(fixation for fixation in regions_fixations)
        except:
            first_fixation = None

        try:
            first_emo_fixation = next(fixation for fixation in region_fixations if fixation['target'])
            capture_delay_emo_first = first_good_fixation['begin'].getTime() - start_trial_time
        except:
            first_emo_fixation = None
            capture_delay_emo_first = None

        try:
            first_neu_fixation = next(fixation for fixation in region_fixations if not fixation['target'])
            capture_delay_neu_first = first_neu_fixation['begin'].getTime() - start_trial_time
        except:
            first_neu_fixation = None
            capture_delay_neu_first = None

        # Time on target and distractors
        total_emo_fixation_time = sum(x['time'] for x in region_fixations if x['target'])
        if total_emo_fixation_time == 0:
            total_emo_fixation_time = None
        total_neu_fixation_time = sum(x['time'] for x in region_fixations if not x['target'])
        if total_neu_fixation_time == 0:
            total_neu_fixation_time = None

        # Determining blink category
        if trial.blinks == []:
            blink_category = "No blink"
        else:
            if first_fixation != None:
                if trial.blinks[0].getStartTime() < first_fixation['begin'].getTime():
                    blink_category = "early capture"
                else:
                    blink_category = "late"
            else:
                blink_category = None

        # Error :
        if (not trial.isStartValid(self.eyetracker.screen_center, self.eyetracker.valid_distance_center)
            or blink_category == 'early capture'):
            #or capture_delay_first < 100):
            error = '#N/A'
        else:
            if ((first_fixation['target'] and trial.features['arrow'] == trial.features['target_side'])
                or (not first_fixation['target'] and trial.features['arrow'] != trial.features['target_side'])):
                error = '0'
            else:
                error = '1'

        # Writing data in result csv file
        s = [str(subject.id) + "-E", # Subject name
            subject.group,
            trial_number,
            #trial.features['session'],
            trial.features['training'],
            trial.eye,
            trial.features['emotion'],
            trial.features['stim1'],
            trial.features['stim2'],
            trial.features['target_side'],
            trial.features['arrow'],
            trial.features['position_emo'],
            trial.features['position_neu'],
            error,
            capture_delay_emo_first,
            capture_delay_neu_first,
            total_emo_fixation_time,
            total_neu_fixation_time,
            blink_category]

        if filename is None:
            f = open(getResultsFile(), 'a')
        else:
            f = open(filename, 'a')
        f.write(';'.join([str(x) for x in s]))
        f.write('\n')
        f.close()

    @staticmethod
    def getDefaultResultsFile():
        return joinPaths(getResultsFolder(), 'visual_selection.csv')

    @staticmethod
    def makeResultFile() -> None:
        createResultsFolder()
        Visual_selection.makeResultFile(getDefaultResultsFile)

    @staticmethod
    def makeResultFile(filename: str) -> None:
        f = open(filename, 'w')
        f.write(';'.join([
            'Subject',
            'Group',
            'TrialID',
            'Training',
            'Eye',
            'Emotion',
            'Emotion target',
            'Neutral target',
            'TargetSide',
            'Arrow orientation',
            'Position emo',
            'Position neu',
            'Errors',
            'First time on emotional target',
            'First time on neutral target',
            'Total fixation time on emotional target',
            'Total fixation time on neutral target',
            'First blink type'
        ]))
        f.write('\n')
        f.close()


    # Creates an image scanpath for one trial.
    def scanpath(self, subject_id, trial, frequency : int):
        plt.clf()

        frame_color = (0,0,0)
        emo_color = (1,0,0)
        x_axis = self.eyetracker.screen_center[0] * 2
        y_axis = self.eyetracker.screen_center[1] * 2
        plt.axis([0, x_axis, 0, y_axis])
        plt.gca().invert_yaxis()
        plt.axis('off')

        # Plotting frames
        if trial.features['position_emo'] == '-300':
            plotRegion(self.eyetracker.left, emo_color)
            plotRegion(self.eyetracker.right, frame_color)
        elif trial.features['position_emo'] == '300':
            plotRegion(self.eyetracker.left, frame_color)
            plotRegion(self.eyetracker.right, emo_color)

        if trial.features['arrow'] == 'left':
            plt.arrow(self.eyetracker.screen_center[0]+10, self.eyetracker.screen_center[1]-2, -20, 4)
        elif trial.features['arrow'] == 'right':
            plt.arrow(self.eyetracker.screen_center[0]-10, self.eyetracker.screen_center[1]-2, 20, 4)

        # Plotting gaze positions
        trial.plot(frequency)
        image_name = 'subject_%i_trial_%i.png' % (subject_id, trial.getTrialId())
        saveImage(getTmpFolder(), image_name)
        return image_name

    # Creates a video scanpath for one trial.
    def scanpathVideo(self, subject_id, trial, frequency : int, progress = None):
        n_elem_drawn = 20
        point_list = trial.getGazePoints()
        nb_points = len(point_list)
        frame_color = (0,0,0)
        point_color = (1,1,0)

        # Taking frequency into account
        point_list_f = []
        for i in range(0,len(point_list)-frequency,frequency):
            point_list_f.append(point_list[i])

        image_list = []

        axis_x = self.eyetracker.screen_center[0]*2
        axis_y = self.eyetracker.screen_center[1]*2

        logTrace ('Creating video frames', Precision.NORMAL)

        if progress != None:
            progress.setText(0, 'Loading frames')
            progress.setMaximum(0, len(point_list_f) - 1)

        for elem in range(0,len(point_list_f)-1):
            if progress != None:
                progress.increment(0)
            plt.clf()
            plt.axis([0,axis_x,0,axis_y])
            plt.gca().invert_yaxis()
            plt.axis('off')

            for j in range(max(0,elem-n_elem_drawn),elem+1):
                plotSegment(point_list_f[j], point_list_f[j+1], c = point_color)
            point_color = (1, point_color[1] - 1.0/nb_points , 0)

            if trial.features['position_emo'] == '-300':
                plotRegion(self.eyetracker.left, emo_color)
                plotRegion(self.eyetracker.right, frame_color)
            elif trial.features['position_emo'] == '300':
                plotRegion(self.eyetracker.left, frame_color)
                plotRegion(self.eyetracker.right, emo_color)

            if trial.features['arrow'] == 'left':
                plt.arrow(self.eyetracker.screen_center[0]+10, self.eyetracker.screen_center[1]-2, -20, 4)
            elif trial.features['arrow'] == 'right':
                plt.arrow(self.eyetracker.screen_center[0]-10, self.eyetracker.screen_center[1]-2, 20, 4)

            image_name = '%i.png' % elem
            saveImage(getTmpFolder(), image_name)
            image_list.append(joinPaths(getTmpFolder(), image_name))
        vid_name = 'subject_%i_trial_%s.avi' % (subject_id, trial.getTrialId())
        progress.setText(0, 'Loading frames')
        makeVideo(image_list, vid_name, fps=100/frequency)
        return vid_name

    def getSubjectData(self, line: str) -> Union[Tuple[int,str]]:
        try:
            l = re.split("[\t ]+", line)
            return (int(l[1]), l[2])
        except:
            return None

    def processSubject(self, input_file : str, progress = None) -> Subject:

        self.selectEyetracker(input_file)

        with open(input_file) as f:
            first_line = f.readline()
            if first_line[-1] == '\n':
                first_line = first_line[:-1]

        subject_data = self.getSubjectData(first_line)

        if subject_data is None:
            raise ExperimentException('Subject number and category could not be found')

        else:
            result_file = "results.txt"
            is_processed = self.eyetracker.preprocess(input_file, result_file, progress)
            if is_processed:
                datafile = open(joinPaths(getTmpFolder(), result_file), "r")
            else:
                datafile = open(input_file, "r")

            #File conversion in list.
            data = datafile.read()
            data = list(data.splitlines())

            #We add a tabulation and space separator.
            data = [re.split("[\t ]+",line) for line in data]

            (n_subject, subject_cat) = subject_data
            return Subject(self, data, n_subject, subject_cat, progress)
