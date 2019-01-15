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
        self.valid_distance_center = 125 #3 degres of visual angle 95 (+ marge)

        # Initializing regions of interest
        self.half_width = 153
        self.half_height = 108

        # frames
        self.frame_list_1 = InterestRegionList([
            InterestRegion((164, 384), self.half_width, self.half_height, 'RECTANGLE'),
            InterestRegion((860, 384), self.half_width, self.half_height, 'RECTANGLE')
        ])

        self.frame_list_3 = InterestRegionList([
            InterestRegion((266, 630), self.half_width, self.half_height, 'RECTANGLE'),
            InterestRegion((758, 630), self.half_width, self.half_height, 'RECTANGLE'),
            InterestRegion((266, 138), self.half_width, self.half_height, 'RECTANGLE'),
            InterestRegion((758, 138), self.half_width, self.half_height, 'RECTANGLE')
        ])

        self.frame_list_5 = InterestRegionList([
            InterestRegion((164, 384), self.half_width, self.half_height, 'RECTANGLE'),
            InterestRegion((860, 384), self.half_width, self.half_height, 'RECTANGLE'),
            InterestRegion((266, 630), self.half_width, self.half_height, 'RECTANGLE'),
            InterestRegion((758, 630), self.half_width, self.half_height, 'RECTANGLE'),
            InterestRegion((266, 138), self.half_width, self.half_height, 'RECTANGLE'),
            InterestRegion((758, 138), self.half_width, self.half_height, 'RECTANGLE')
        ])

        # Patients with inhibition difficulties
        self.list_patients_cong = [13,14]

    # Returns a dictionary of experiment variables
    def parseVariables(self, line: List[str]):
        if len(line) > 24 and line[8] == "tgt_hor":
            try:
                if len(line) > 24 and line[8] == "tgt_hor":
                    target_hp = int(line[10]) + self.screen_center[0]
                    target_vp = int(line[15]) + self.screen_center[1]
                    num_of_dis = int(line[5])
                    cor_resp = int(line[20])
                    response = int(line[24])
                    if target_hp < self.screen_center[0]:
                        target_side = "L"
                    else:
                        target_side = "R"
                return {
                    'target_hp' : target_hp,
                    'target_vp' : target_vp,
                    'num_of_dis' : num_of_dis,
                    'cor_resp' : cor_resp,
                    'response' : response,
                    'target_side' : target_side
                }
            except:
                pass
        return None

    def isResponse(self, line: Line) -> bool :
        return len(line) >= 6 and 'repondu' in line[5]

    def isTraining(self, trial) -> bool:
        return 'face' in trial.getStimulus()

class Gaze_contingent(Experiment):

    def __init__(self):
        super().__init__(None)
        self.n_trials = 120

    def selectEyetracker(self, input_file : str) -> None:
        logTrace ('Selecting Eyelink', Precision.NORMAL)
        self.eyetracker = Make_Eyelink()

    def processTrial(self, subject, trial, filename = None):
        logTrace ('Processing trial n°%i' % trial.getTrialId(), Precision.DETAIL)
        trial_number = trial.getTrialId()

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
            'Block',
            'Eye',
            'Emotion',
            'TargetName',
            'Number of Distractors',
            'Target X position',
            'Target Y position',
            'Target side',
            'Congruency',
            'Correct response',
            'Response',
            'Errors',
            'Response time',
            'First localization time',
            'Response delay from last fixation',
            'Total fixation time on target',
            'Total fixation time on distractors',
            'First blink type'
        ]))
        f.write('\n')
        f.close()

    @staticmethod
    def plotTarget(region: InterestRegion, cor_resp, color):
    	lu_corner = [region.center[0]-region.half_width, region.center[1]+region.half_height]
    	lb_corner = [region.center[0]-region.half_width, region.center[1]-region.half_height]
    	ru_corner = [region.center[0]+region.half_width, region.center[1]+region.half_height]
    	rb_corner = [region.center[0]+region.half_width, region.center[1]-region.half_height]

    	if cor_resp == 2:
    		hole_up = [region.center[0]+region.half_width, region.center[1]+30]
    		hole_down = [region.center[0]+region.half_width, region.center[1]-30]
    		plotSegment(lu_corner, lb_corner, c=color)
    		plotSegment(lb_corner, rb_corner, c=color)
    		plotSegment(rb_corner, hole_down, c=color)
    		plotSegment(hole_up, ru_corner, c=color)
    		plotSegment(ru_corner, lu_corner, c=color)

    	elif cor_resp == 1:
    		hole_up = [region.center[0]-region.half_width, region.center[1]+30]
    		hole_down = [region.center[0]-region.half_width, region.center[1]-30]
    		plotSegment(lb_corner, rb_corner, c=color)
    		plotSegment(rb_corner, ru_corner, c=color)
    		plotSegment(ru_corner, lu_corner, c=color)
    		plotSegment(lb_corner, hole_down, c=color)
    		plotSegment(hole_up, lu_corner, c=color)

    # Creates an image scanpath for one trial.
    def scanpath(self, subject_id, trial):
        plt.clf()

        frame_color = (0,0,0)
        target_color = (1,0,0)
        x_axis = self.eyetracker.screen_center[0] * 2
        y_axis = self.eyetracker.screen_center[1] * 2
        plt.axis([0, x_axis, 0, y_axis])
        plt.gca().invert_yaxis()
        plt.axis('off')

        # Plotting frames
        if trial.features['num_of_dis'] == 1:
            frame_list = self.eyetracker.frame_list_1.getRegions()
        elif trial.features['num_of_dis'] == 3:
            frame_list = self.eyetracker.frame_list_3.getRegions()
        elif trial.features['num_of_dis'] == 5:
            frame_list = self.eyetracker.frame_list_5.getRegions()

        for frame in frame_list:
            if frame.isTarget((trial.features['target_hp'], trial.features['target_vp'])):
                Gaze_contingent.plotTarget(frame, trial.features['cor_resp'], target_color)
            else:
                plotRegion(frame, frame_color)

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
        target_color = (1,0,0)
        point_color = (1,1,0)

        image_list = []
        # Plotting frames
        if trial.features['num_of_dis'] == 1:
            frame_list = self.eyetracker.frame_list_1.getRegions()
        elif trial.features['num_of_dis'] == 3:
            frame_list = self.eyetracker.frame_list_3.getRegions()
        elif trial.features['num_of_dis'] == 5:
            frame_list = self.eyetracker.frame_list_5.getRegions()

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

            for frame in frame_list:
                if frame.isTarget((trial.features['target_hp'], trial.features['target_vp'])):
                    Recherche_visuelle.plotTarget(frame, trial.features['cor_resp'], target_color)
                else:
                    plotRegion(frame, frame_color)

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
