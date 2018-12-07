import re #To format data lists
from eyetracking.eyelink import *
from eyetracking.smi import *
from eyetracking.experiment import *
from eyetracking.interest_region import *
from eyetracking.scanpath import *
import matplotlib.pyplot as plt

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
            InterestRegion((164, 384), self.half_width, self.half_height),
            InterestRegion((860, 384), self.half_width, self.half_height)
        ])

        self.frame_list_3 = InterestRegionList([
            InterestRegion((266, 630), self.half_width, self.half_height),
            InterestRegion((758, 630), self.half_width, self.half_height),
            InterestRegion((266, 138), self.half_width, self.half_height),
            InterestRegion((758, 138), self.half_width, self.half_height)
        ])

        self.frame_list_5 = InterestRegionList([
            InterestRegion((164, 384), self.half_width, self.half_height),
            InterestRegion((860, 384), self.half_width, self.half_height),
            InterestRegion((266, 630), self.half_width, self.half_height),
            InterestRegion((758, 630), self.half_width, self.half_height),
            InterestRegion((266, 138), self.half_width, self.half_height),
            InterestRegion((758, 138), self.half_width, self.half_height)
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

class Make_Smi(Smi):
    def __init__(self):
        super().__init__()
        # Center of the screen.
        self.screen_center = (683,384)
        # Minimal distance at which we consider the subject is looking at the
        # fixation cross at the trial beginning
        self.valid_distance_center = 130 #3 degres of visual angle 95 (+ marge)

        # Initializing regions of interest
        self.half_width = 163
        self.half_height = 115

        # frames
        self.frame_list_1 = InterestRegionList([
            InterestRegion((312, 384), self.half_width, self.half_height),
            InterestRegion((1054, 384), self.half_width, self.half_height)
        ])

        self.frame_list_3 = InterestRegionList([
            InterestRegion((421, 646), self.half_width, self.half_height),
            InterestRegion((945, 646), self.half_width, self.half_height),
            InterestRegion((945, 122), self.half_width, self.half_height),
            InterestRegion((421, 122), self.half_width, self.half_height)
        ])

        self.frame_list_5 = InterestRegionList([
            InterestRegion((312, 384), self.half_width, self.half_height),
            InterestRegion((1054, 384), self.half_width, self.half_height),
            InterestRegion((421, 646), self.half_width, self.half_height),
            InterestRegion((945, 646), self.half_width, self.half_height),
            InterestRegion((945, 122), self.half_width, self.half_height),
            InterestRegion((421, 122), self.half_width, self.half_height)
        ])

        # Patients with inhibition difficulties
        self.list_patients_cong = [45, 50, 51, 53]

    # Returns a dictionary of experiment variables
    def parseVariables(self, line: List[str]):
        print(line)
        if len(line) > 6 and line[5] == "features:":
            try:
                target_hp = int(line[9]) + self.screen_center[0]
                target_vp = int(line[11]) + self.screen_center[1]
                num_of_dis = int(line[7])
                cor_resp = int(line[13])
                response = int(line[15])
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
        return len(line) >= 8 and 'sujet' in line[6]

    def isTraining(self, trial) -> bool:
        return 'face' in trial.getStimulus()


class Recherche_visuelle(Experiment):

    def __init__(self, eyetracker):
        super().__init__(eyetracker)
        self.n_trials = 120

    def processTrial(self, subject, trial):
        print('Processing trial n°%i' % trial.getTrialId())
        trial_number = trial.getTrialId()

        if trial.saccades == []:
            print(subject.subject_number,trial_number,"Subject has no saccades!")

        if trial.features['num_of_dis'] == 1:
            frame_list = self.eyetracker.frame_list_1
        elif trial.features['num_of_dis'] == 3:
            frame_list = self.eyetracker.frame_list_3
        elif trial.features['num_of_dis'] == 5:
            frame_list = self.eyetracker.frame_list_5

        start_trial_time = trial.getStartTrial().getTime()

        targetname = trial.getStimulus()

        response_entry = trial.getResponse()

        response_time = response_entry.getTime() - trial.getStartTrial().getTime()

        target_region_position = (trial.features["target_hp"], trial.features["target_vp"])

        region_fixations = trial.getFixationTime(frame_list, frame_list.point_inside(target_region_position))

        total_target_fixation_time = sum(x['time'] for x in region_fixations if x['target'])
        if total_target_fixation_time == 0:
            total_target_fixation_time = None

        if "mtemo" in targetname:
            target_cat = "EMO"
        elif "mtneu" in targetname:
            target_cat = "NEU"
        elif "face" in targetname:
            target_cat = "VISAGE"
        else:
            target_cat = None

        #We determine in which block occurred each trial
        block = None
        if int(trial_number) < 60 and target_cat != "VISAGE":
            block = 1
        elif int(trial_number) >= 60:
            block = 2

        #We determine congruency between target side and frame break side.
        congruency = None
        if ((trial.features['target_hp'] < self.eyetracker.screen_center[0] and trial.features['cor_resp'] == 1)
        or (trial.features['target_hp'] > self.eyetracker.screen_center[0] and trial.features['cor_resp'] == 2)):
            congruency = "YES"
        else:
            congruency = "NO"

        # First and last good fixations
        try:
            first_good_fixation = next(fixation for fixation in region_fixations if fixation['target'])
            last_good_fixation = next(fixation for fixation in reversed(region_fixations) if fixation['target'])
            response_delay_last = response_time - (last_good_fixation['begin'].getTime() - start_trial_time)
            # Delay of capture to the first good fixation
            capture_delay_first = first_good_fixation['begin'].getTime() - start_trial_time
        except:
            first_good_fixation = None
            last_good_fixation = None
            response_delay_last = None
            capture_delay_first = None

        # Time on target and distractors
        total_target_fixation_time = sum(x['time'] for x in region_fixations if x['target'])
        if total_target_fixation_time == 0:
            total_target_fixation_time = None
        total_distractor_fixation_time = sum(x['time'] for x in region_fixations if not x['target'])
        if total_distractor_fixation_time == 0:
            total_distractor_fixation_time = None

        # Determining blink category
        if trial.blinks == []:
            blink_category = "No blink"
        else:
            if trial.blinks[0].getStartTime() < first_good_fixation['begin'].getTime():
                blink_category = "early capture"
            else:
                blink_category = "late"

        # Error :
        if (not trial.isStartValid(self.eyetracker.screen_center, self.eyetracker.valid_distance_center)
            or first_good_fixation == None
            or trial.features['response'] == 'None'
            or blink_category == 'early capture'
            or capture_delay_first < 100):
            error = '#N/A'
        elif (subject.group == 'MA'
            and subject in list_patients_cong
            and congruency == "NO"
            and trial.features['cor_resp'] != trial.features['response']):
            error = 'CONG'
        else:
            if trial.features['cor_resp'] != trial.features['response']:
                error = '1'
            else:
                error = '0'

        # Writing data in result csv file
        s = [str(subject.id) + "-E", # Subject name
            subject.group,
            trial_number,
            block,
            trial.eye,
            target_cat,
            targetname,
            trial.features['num_of_dis'],
            trial.features['target_hp'],
            trial.features['target_vp'],
            trial.features['target_side'],
            congruency,
            trial.features['cor_resp'],
            trial.features['response'],
            error,
            response_time,
            capture_delay_first,
            response_delay_last,
            total_target_fixation_time,
            total_distractor_fixation_time,
            blink_category]

        print(s)

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
    def scanpath(self, subject_id, trial, folder):
        print('scanpath')
        print(trial.features)

        plt.clf()

        frame_color = (0,0,0)
        target_color = (1,0,0)
        plt.axis([0,1024,0,768])
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
                Recherche_visuelle.plotTarget(frame, trial.features['cor_resp'], target_color)
            else:
                plotRegion(frame, frame_color)

        # Plotting gaze positions
        trial.plot()
        image_name = '%i_%i.png' % (subject_id, trial.getTrialId())
        saveImage(getTmpFolder(), image_name)

    # Creates a video scanpath for one trial.
    def scanpathVideo(self, subject_id, trial):
        print('scanpath video')
        print(trial.features)

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
        print('Creating video frames')
        for elem in range(0,len(point_list)-1):
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
        makeVideo(image_list, 'test_vid.avi', fps=100)

    def getSubjectData(self, line: str) -> Union[Tuple[int,str]]:
        try:
            l = re.split("[\t ]+", line)
            return (int(l[1]), l[2])
        except:
            return None

    def processSubject(self, input_file : str, progress_bar = None) -> Subject:
        with open(input_file) as f:
            first_line = f.readline()

        print(first_line)
        subject_data = self.getSubjectData(first_line)

        if subject_data is None:
            return None

        else:
            result_file = "results.txt"
            is_processed = self.eyetracker.preprocess(input_file, result_file)
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
            return Subject(self, data, n_subject, subject_cat, progress_bar)
