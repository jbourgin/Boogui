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
        self.half_width = 128 #170
        self.half_height = 128 #170

        # frames
        self.right = RectangleRegion((self.screen_center[0]*1.5, self.screen_center[1]), self.half_width, self.half_height)
        self.left = RectangleRegion((self.screen_center[0]/2, self.screen_center[1]), self.half_width, self.half_height)

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

    def isResponse(self, line: Line) -> bool :
        return len(line) >= 5 and 'END' in line[2] and 'TRANSITION' in line[3] and 'TIMEOUT' in line[4]
    def isTraining(self, trial) -> bool:
        return 'App' in trial.features['training']

    def parseStartTrial(self, line: List[str]) -> Union[Entry, None]:
        if len(line) >= 4 and line[2] == 'BEGIN' and line[3] == 'TRANSITION' and line[4] == 'time_transition':
            try:
                time = int(line[1])
                trial_number = int(line[-1])
                stimulus = line[8]
                return Entry.Start_trial(time, trial_number, stimulus)
            except:
                pass
        return None

    def parseStopTrial(self, line: List[str]) -> Union[Entry, None]:
        if len(line) >= 4 and line[2] == 'END' and line[3] == 'SEQUENCE':
            try:
                time = int(line[1])
                return Entry.Stop_trial(time)
            except:
                pass
        return None

class Prosaccade(Experiment):

    def __init__(self):
        super().__init__(None)
        self.n_trials = 96

    def selectEyetracker(self, input_file : str) -> None:
        logTrace ('Selecting Eyelink', Precision.NORMAL)
        self.eyetracker = Make_Eyelink()

    def processTrial(self, subject, trial, filename = None):
        pass

        logTrace ('Processing trial n°%i' % trial.getTrialId(), Precision.DETAIL)
        trial_number = trial.getTrialId()
        targetname = trial.getStimulus()

        if trial.saccades == []:
            logTrace ('Subject %i has no saccades at trial %i !' %(subject.id,trial_number), Precision.DETAIL)
        else:
            if trial.features['target_side'] == 'Gauche':
                correct_position = 'Left'
                target_position = self.eyetracker.left
            elif trial.features['target_side'] == 'Droite':
                correct_position = 'Right'
                target_position = self.eyetracker.right
            regions = InterestRegionList(target_position)

            start_trial_time = trial.getStartTrial().getTime()

            if 'Neg' in targetname[:2]:
                emotion = 'Negative'
            elif 'P' in targetname[0]:
                emotion = 'Positive'
            elif 'Neu' in targetname[:2]:
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
            if (not trial.isStartValid(self.eyetracker.screen_center, self.eyetracker.valid_distance_center)
                or blink_category == 'early capture'
                or SRT_real <= 80
                or sac_duration < 22
                or sac_amplitude < self.eyetracker.valid_distance_center):
                #or capture_delay_first < 100):
                error = '#N/A'
            elif ((correct_position == 'Right'
                  and horizontal_gaze_position_end < self.eyetracker.screen_center[0])
                  or (correct_position == 'Left'
                      and horizontal_gaze_position_end > self.eyetracker.screen_center[0])):
                error = '1'
            elif ((correct_position == 'Right'
                  and horizontal_gaze_position_end > self.eyetracker.screen_center[0])
                  or (correct_position == 'Left'
                      and horizontal_gaze_position_end < self.eyetracker.screen_center[0])):
                error = '0'
            else:
                error = None

        # Writing data in result csv file
        s = [str(subject.id) + '-E', # Subject name
            subject.group,
            trial_number,
            trial.features['training'],
            trial.eye,
            emotion,
            targetname,
            trial.features['target_side'],
            correct_position,
            error,
            trial.saccades[0].getStartTime() - start_trial_time,
            trial.saccades[0].getFirstGazePosition(),
            trial.saccades[0].getLastGazePosition(),
            blink_category,
            threshold_excess]

        if filename is None:
            f = open(getResultsFile(), 'a')
        else:
            f = open(filename, 'a')
        f.write(';'.join([str(x) for x in s]))
        f.write('\n')
        f.close()

    @staticmethod
    def getDefaultResultsFile():
        return joinPaths(getResultsFolder(), 'antisaccade.csv')

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
            'Target Name',
            'TargetSide',
            'Correct position',
            'Errors',
            'First saccade RT',
            'First saccade start gaze position',
            'First saccade ending gaze position',
            'First blink type',
            'Threshold excess'
        ]))
        f.write('\n')
        f.close()

    # Creates an image scanpath for one trial.
    def scanpath(self, subject_id, trial, frequency : int):
        plt.clf()

        if 'P' in trial.getStimulus()[0]:
            frame_color = (0,1,0)
        elif 'Neg' in trial.getStimulus()[:2]:
            frame_color = (1,0,0)
        else:
            frame_color = (0,0,0)

        x_axis = self.eyetracker.screen_center[0] * 2
        y_axis = self.eyetracker.screen_center[1] * 2
        plt.axis([0, x_axis, 0, y_axis])
        plt.gca().invert_yaxis()
        plt.axis('off')

        # Plotting frames
        if trial.features['target_side'] == 'Gauche':
            plotRegion(self.eyetracker.left, frame_color)
        elif trial.features['target_side'] == 'Droite':
            plotRegion(self.eyetracker.right, frame_color)

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
        point_color = (1,1,0)

        if 'P' in trial.getStimulus()[0]:
            frame_color = (0,1,0)
        elif 'Neg' in trial.getStimulus()[:2]:
            frame_color = (1,0,0)
        else:
            frame_color = (0,0,0)

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

            if trial.features['target_side'] == 'Gauche':
                plotRegion(self.eyetracker.left, frame_color)
            elif trial.features['target_side'] == 'Droite':
                plotRegion(self.eyetracker.right, frame_color)

            image_name = '%i.png' % elem
            saveImage(getTmpFolder(), image_name)
            image_list.append(joinPaths(getTmpFolder(), image_name))
        vid_name = 'subject_%i_trial_%s.avi' % (subject_id, trial.getTrialId())
        progress.setText(0, 'Loading frames')
        makeVideo(image_list, vid_name, fps=100/frequency)
        return vid_name

    def getSubjectData(self, line: str) -> Union[Tuple[int,str]]:
        try:
            l = re.split('[\t ]+', line)
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
            result_file = 'results.txt'
            is_processed = self.eyetracker.preprocess(input_file, result_file, progress)
            if is_processed:
                datafile = open(joinPaths(getTmpFolder(), result_file), 'r')
            else:
                datafile = open(input_file, 'r')

            #File conversion in list.
            data = datafile.read()
            data = list(data.splitlines())

            #We add a tabulation and space separator.
            data = [re.split('[\t ]+',line) for line in data]

            (n_subject, subject_cat) = subject_data
            return Subject(self, data, n_subject, subject_cat, progress)
