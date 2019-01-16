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
        self.screen_center = (960,540)
        # Minimal distance at which we consider the subject is looking at the
        # fixation cross at the trial beginning
        self.valid_distance_center = 140 #3 degres of visual angle 95 (+ marge)

        # Initializing regions of interest
        self.half_width = 182
        self.half_height_face = 232
        self.half_height_eye = 45

        # frames
        self.right_gaze = InterestRegion((self.screen_center[0]*1.5, self.screen_center[1]+10), self.half_width, self.half_height_eye, 'RECTANGLE')
        self.left_gaze = InterestRegion((self.screen_center[0]/2.0, self.screen_center[1]+10), self.half_width, self.half_height_eye, 'RECTANGLE')
        self.right_face = InterestRegion((self.screen_center[0]*1.5, self.screen_center[1]), self.half_width, self.half_height_face, 'ELLIPSE')
        self.left_face = InterestRegion((self.screen_center[0]/2.0, self.screen_center[1]), self.half_width, self.half_height_face, 'ELLIPSE')

    # Returns a dictionary of experiment variables
    # REAL ONE :
    '''
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
                    response_time = float(line[12])

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
    '''

    # FAKE NEWS
    def parseVariables(self, line: List[str]):
        if len(line) > 5 and line[2] == "Main":
            line = [x.replace(',','') for x in line]
            try:
                training = 'MONZBI'
                global_task = line[4]
                emotion = line[5]
                gender = line[6]
                target_side = line[7]
                response = line[8]
                cor_resp = line[9]
                response_time = line[10]

                return {
                    'training' : training,
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
        logTrace('isTraining to fix!', Precision.TITLE)
        return False
    #    return 'Training' in trial.features['training']

class Gaze_contingent(Experiment):

    def __init__(self):
        super().__init__(None)
        logTrace('Attention: nombre d''essais à changer', Precision.TITLE)
        self.n_trials = 96

    def selectEyetracker(self, input_file : str) -> None:
        logTrace ('Selecting Eyelink', Precision.NORMAL)
        self.eyetracker = Make_Eyelink()

    def processTrial(self, subject, trial, filename = None):
        logTrace ('Processing trial n°%i' % trial.getTrialId(), Precision.DETAIL)
        trial_number = trial.getTrialId()

        ####################

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
            'Task',
            'Session',
            'Eye',
            'Emotion',
            'TargetName',
            'Genre',
            'Target Side',
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
    def scanpath(self, subject_id, trial):
        plt.clf()

        frame_color = (0,0,0)
        x_axis = self.eyetracker.screen_center[0] * 2
        y_axis = self.eyetracker.screen_center[1] * 2
        plt.axis([0, x_axis, 0, y_axis])
        plt.gca().invert_yaxis()
        plt.axis('off')

        # Plotting frames
        if trial.features['target_side'] == 'Left':
            plotRegion(self.eyetracker.left_face, frame_color)
            plotRegion(self.eyetracker.left_gaze, frame_color)
        elif trial.features['target_side'] == 'Right':
            plotRegion(self.eyetracker.right_face, frame_color)
            plotRegion(self.eyetracker.right_gaze, frame_color)

        # Plotting gaze positions
        trial.plot()
        image_name = 'subject_%i_trial_%i.png' % (subject_id, trial.getTrialId())
        saveImage(getTmpFolder(), image_name)
        return image_name

    # Creates a video scanpath for one trial.
    def scanpathVideo(self, subject_id, trial, progress = None):
        n_elem_drawn = 20
        point_list = trial.getGazePoints()
        nb_points = len(point_list)
        frame_color = (0,0,0)
        point_color = (1,1,0)

        image_list = []

        axis_x = self.eyetracker.screen_center[0]*2
        axis_y = self.eyetracker.screen_center[1]*2

        logTrace ('Creating video frames', Precision.NORMAL)

        if progress != None:
            progress.setText(0, 'Loading frames')
            progress.setMaximum(0, len(point_list) - 1)

        for elem in range(0,len(point_list)-1):
            if progress != None:
                progress.increment(0)
            plt.clf()
            plt.axis([0,axis_x,0,axis_y])
            plt.gca().invert_yaxis()
            plt.axis('off')

            for j in range(max(0,elem-n_elem_drawn),elem+1):
                plotSegment(point_list[j], point_list[j+1], c = point_color)
            point_color = (1, point_color[1] - 1.0/nb_points , 0)

            if trial.features['target_side'] == 'Left':
                plotRegion(self.eyetracker.left_face, frame_color)
                plotRegion(self.eyetracker.left_gaze, frame_color)
            elif trial.features['target_side'] == 'Right':
                plotRegion(self.eyetracker.right_face, frame_color)
                plotRegion(self.eyetracker.right_gaze, frame_color)

            image_name = '%i.png' % elem
            saveImage(getTmpFolder(), image_name)
            image_list.append(joinPaths(getTmpFolder(), image_name))
        vid_name = 'subject_%i_trial_%s.avi' % (subject_id, trial.getTrialId())
        progress.setText(0, 'Loading frames')
        makeVideo(image_list, vid_name, fps=100)
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
