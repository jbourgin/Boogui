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
        self.screen_center = (960,600)
        # Minimal distance at which we consider the subject is looking at the
        # fixation cross at the trial beginning
        self.valid_distance_center = 140 #3 degres of visual angle 95 (+ marge)

        # Initializing regions of interest
        self.half_width = 182
        self.half_height_face = 232
        self.half_height_eye = 45

        # frames
        self.right_gaze = RectangleRegion((self.screen_center[0]*1.5, self.screen_center[1]+10), self.half_width, self.half_height_eye)
        self.left_gaze = RectangleRegion((self.screen_center[0]/2.0, self.screen_center[1]+10), self.half_width, self.half_height_eye)
        self.right_ellipse = EllipseRegion((self.screen_center[0]*1.5, self.screen_center[1]), self.half_width, self.half_height_face)
        self.left_ellipse = EllipseRegion((self.screen_center[0]/2.0, self.screen_center[1]), self.half_width, self.half_height_face)
        self.right_face = DifferenceRegion(self.right_ellipse, self.right_gaze)
        self.left_face = DifferenceRegion(self.left_ellipse, self.left_gaze)

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
                    cor_resp = int(line[11])
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
        return len(line) >= 5 and 'showing' in line[4]

    def isTraining(self, trial) -> bool:
        return 'Training' in trial.features['training']

class Gaze_contingent(Experiment):

    def __init__(self):
        super().__init__(None)
        self.n_trials = 96

    def selectEyetracker(self, input_file : str) -> None:
        logTrace ('Selecting Eyelink', Precision.NORMAL)
        self.eyetracker = Make_Eyelink()

    def processTrial(self, subject, trial, filename = None):
        logTrace ('Processing trial n°%i' % trial.getTrialId(), Precision.DETAIL)
        trial_number = trial.getTrialId()

        if trial.saccades == []:
            logTrace ("Subject %i has no saccades at trial %i !" %(subject.id,trial_number), Precision.DETAIL)

        if trial.features['target_side'] == 'Left':
            gaze_position = self.eyetracker.left_gaze
            face_position = self.eyetracker.left_face
        elif trial.features['target_side'] == 'Right':
            gaze_position = self.eyetracker.right_gaze
            face_position = self.eyetracker.right_face
        regions = InterestRegionList([gaze_position, face_position])

        start_trial_time = trial.getStartTrial().getTime()

        targetname = trial.getStimulus()

        response_entry = trial.getResponse()

        region_fixations = trial.getFixationTime(regions, gaze_position)

        # First and last good fixations
        try:
            first_good_fixation = next(fixation for fixation in region_fixations if fixation['target'])
            capture_delay_first = first_good_fixation['begin'].getTime() - start_trial_time
        except:
            first_good_fixation = None
            capture_delay_first = None

        # Time on target and distractors
        total_eye_fixation_time = sum(x['time'] for x in region_fixations if x['target'])
        if total_eye_fixation_time == 0:
            total_eye_fixation_time = None
        total_faceNotEye_fixation_time = sum(x['time'] for x in region_fixations if not x['target'])
        if total_faceNotEye_fixation_time == 0:
            total_faceNotEye_fixation_time = None

        # Determining blink category
        if trial.blinks == []:
            blink_category = "No blink"
        else:
            if first_good_fixation != None:
                if trial.blinks[0].getStartTime() < first_good_fixation['begin'].getTime():
                    blink_category = "early capture"
                else:
                    blink_category = "late"
            else:
                blink_category = None

        # Error :
        if (not trial.isStartValid(self.eyetracker.screen_center, self.eyetracker.valid_distance_center)
            or trial.features['response'] == 'None'
            or blink_category == 'early capture'):
            #or capture_delay_first < 100):
            error = '#N/A'
        else:
            if trial.features['cor_resp'] != trial.features['response']:
                error = '1'
            else:
                error = '0'

        # Writing data in result csv file
        s = [str(subject.id) + "-E", # Subject name
            subject.group,
            trial_number,
            #trial.features['session'],
            trial.features['training'],
            trial.features['global_task'],
            trial.eye,
            trial.features['emotion'],
            trial.features['gender'],
            targetname,
            trial.features['target_side'],
            trial.features['cor_resp'],
            trial.features['response'],
            error,
            trial.features['response_time'],
            capture_delay_first,
            total_eye_fixation_time,
            total_faceNotEye_fixation_time,
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
        return joinPaths(getResultsFolder(), 'gaze_contingent.csv')

    @staticmethod
    def makeResultFile() -> None:
        createResultsFolder()
        Gaze_contingent.makeResultFile(getDefaultResultsFile)

    @staticmethod
    def makeResultFile(filename: str) -> None:
        f = open(filename, 'w')
        f.write(';'.join([
            'Subject',
            'Group',
            'TrialID',
            #'Session',
            'Training',
            'Task',
            'Eye',
            'Emotion',
            'Gender',
            'TargetName',
            'TargetSide',
            'Correct response',
            'Response',
            'Errors',
            'Response time',
            'First time on eyes',
            'Total fixation time on eyes',
            'Total fixation time on face (other than eyes)',
            'First blink type'
        ]))
        f.write('\n')
        f.close()


    # Creates an image scanpath for one trial.
    def scanpath(self, subject_id, trial, frequency : int):
        plt.clf()

        frame_color = (0,0,0)
        x_axis = self.eyetracker.screen_center[0] * 2
        y_axis = self.eyetracker.screen_center[1] * 2
        plt.axis([0, x_axis, 0, y_axis])
        plt.gca().invert_yaxis()
        plt.axis('off')

        # Plotting frames
        if trial.features['target_side'] == 'Left':
            plotRegion(self.eyetracker.left_ellipse, frame_color)
            plotRegion(self.eyetracker.left_gaze, frame_color)
        elif trial.features['target_side'] == 'Right':
            plotRegion(self.eyetracker.right_ellipse, frame_color)
            plotRegion(self.eyetracker.right_gaze, frame_color)

        # Plotting gaze positions
        trial.plot(frequency)
        if trial.isTraining():
            image_name = 'subject_%i_training_%i.png' % (subject_id, trial.getTrialId())
        else:
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

            if trial.features['target_side'] == 'Left':
                plotRegion(self.eyetracker.left_ellipse, frame_color)
                plotRegion(self.eyetracker.left_gaze, frame_color)
            elif trial.features['target_side'] == 'Right':
                plotRegion(self.eyetracker.right_ellipse, frame_color)
                plotRegion(self.eyetracker.right_gaze, frame_color)

            image_name = '%i.png' % elem
            saveImage(getTmpFolder(), image_name)
            image_list.append(joinPaths(getTmpFolder(), image_name))
        if trial.isTraining():
            vid_name = 'subject_%i_training_%s.avi' % (subject_id, trial.getTrialId())
        else:
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
