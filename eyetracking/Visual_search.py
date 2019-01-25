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
        self.eyetracker_name = "Eyelink"
        # Minimal distance at which we consider the subject is looking at the
        # fixation cross at the trial beginning
        self.valid_distance_center = 125 #3 degres of visual angle 95

        # Initializing regions of interest
        self.half_width = 153
        self.half_height = 108

        # frames
        self.frame_list_1 = InterestRegionList([
            RectangleRegion((164, 384), self.half_width, self.half_height),
            RectangleRegion((860, 384), self.half_width, self.half_height)
        ])

        self.frame_list_3 = InterestRegionList([
            RectangleRegion((266, 630), self.half_width, self.half_height),
            RectangleRegion((758, 630), self.half_width, self.half_height),
            RectangleRegion((266, 138), self.half_width, self.half_height),
            RectangleRegion((758, 138), self.half_width, self.half_height)
        ])

        self.frame_list_5 = InterestRegionList([
            RectangleRegion((164, 384), self.half_width, self.half_height),
            RectangleRegion((860, 384), self.half_width, self.half_height),
            RectangleRegion((266, 630), self.half_width, self.half_height),
            RectangleRegion((758, 630), self.half_width, self.half_height),
            RectangleRegion((266, 138), self.half_width, self.half_height),
            RectangleRegion((758, 138), self.half_width, self.half_height)
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
        self.eyetracker_name = "SMI"
        # Minimal distance at which we consider the subject is looking at the
        # fixation cross at the trial beginning
        self.valid_distance_center = 130 #3 degres of visual angle 95 (+ marge)

        # Initializing regions of interest
        self.half_width = 163
        self.half_height = 115

        # frames
        self.frame_list_1 = InterestRegionList([
            RectangleRegion((312, 384), self.half_width, self.half_height),
            RectangleRegion((1054, 384), self.half_width, self.half_height)
        ])

        self.frame_list_3 = InterestRegionList([
            RectangleRegion((421, 646), self.half_width, self.half_height),
            RectangleRegion((945, 646), self.half_width, self.half_height),
            RectangleRegion((945, 122), self.half_width, self.half_height),
            RectangleRegion((421, 122), self.half_width, self.half_height)
        ])

        self.frame_list_5 = InterestRegionList([
            RectangleRegion((312, 384), self.half_width, self.half_height),
            RectangleRegion((1054, 384), self.half_width, self.half_height),
            RectangleRegion((421, 646), self.half_width, self.half_height),
            RectangleRegion((945, 646), self.half_width, self.half_height),
            RectangleRegion((945, 122), self.half_width, self.half_height),
            RectangleRegion((421, 122), self.half_width, self.half_height)
        ])

        # Patients with inhibition difficulties
        self.list_patients_cong = [45, 50, 51, 53]

    # Returns a dictionary of experiment variables
    def parseVariables(self, line: List[str]):
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

class ExperimentException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class Visual_search(Experiment):

    def __init__(self):
        super().__init__(None)
        self.n_trials = 120
        self.expected_features = {'target_hp', 'target_vp', 'num_of_dis', 'cor_resp', 'response', 'target_side'}

    def selectEyetracker(self, input_file : str) -> None:
        eyelink = Make_Eyelink()
        if eyelink.isParsable(input_file):
            logTrace ('Selecting Eyelink', Precision.NORMAL)
            self.eyetracker = eyelink
        else:
            smi = Make_Smi()
            if smi.isParsable(input_file):
                logTrace ('Selecting SMI', Precision.NORMAL)
                self.eyetracker = smi
            else:
                logTrace ('No suitable eyetracker found for input file %s' % input_file, Precision.ERROR)
                raise ExperimentException('No suitable eyetracker found for input file %s' % input_file)

    def processTrial(self, subject, trial, filename = None):
        logTrace ('Processing trial n°%i' % trial.getTrialId(), Precision.DETAIL)
        logTrace ('The first SMI version had a redefinition of frames', Precision.TITLE)
        trial_number = trial.getTrialId()

        if trial.saccades == []:
            logTrace ("Subject %i has no saccades at trial %i !" %(subject.id,trial_number), Precision.DETAIL)

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
            if first_good_fixation != None and trial.blinks[0].getStartTime() < first_good_fixation['begin'].getTime():
                blink_category = "early capture"
            else:
                blink_category = "late"

        # Error :
        if not trial.isStartValid(self.eyetracker.screen_center, self.eyetracker.valid_distance_center):
            error = "Not valid start"
        elif first_good_fixation is None:
            error = "No fixation on target"
        elif trial.features['response'] == 'None':
            error = "No subject response"
        elif blink_category == 'early capture':
            error = "Early blink"
        elif capture_delay_first < 100:
            error = "Anticipation saccade"
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
        if self.eyetracker.eyetracker_name == "Eyelink":
            subject_name = str(subject.id) + "-E"
        elif self.eyetracker.eyetracker_name == "SMI":
            subject_name = str(subject.id) + "-S"
        s = [subject_name, # Subject name
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

        if filename is None:
            f = open(getResultsFile(), 'a')
        else:
            f = open(filename, 'a')
        f.write(';'.join([str(x) for x in s]))
        f.write('\n')
        f.close()

    def postProcess(self, filename: str):
        # In the first version, there was a minimal threshold for the first localization time.
        with open(filename) as datafile:
            data = datafile.read()
        data_modified = open(filename, 'w')
        data = data.split('\n')
        data = [x.split(';') for x in data]
        subject = "Subject"
        sequence = []
        data_seq = []

        for line in data:
            if line[0] == "Subject":
                new_line = line
                new_line.append('First localization sorting')
                new_line.append('Response delay sorting')
                new_line.append('Response time sorting')
                s = ";".join([str(e) for e in new_line]) + "\n"
                data_modified.write(s)
            if line[0] != subject:
                data_seq.append(sequence)
                sequence = [line]
                subject = line[0]
            else:
                sequence.append(line)
        data = data_seq[1:]


        for subject in data:
            sum_dic = {}
            counter_dic = {}
            mean_dic = {}
            SS_dic = {}
            counter_SS_dic = {}
            SD_dic = {}

            for line in subject:
                emotion = line[5]
                distractors = line[7]
                error = line[14]
                response_time = line[15]
                localization_time = line[16]
                response_delay = line[17]
                blink = line[20]
                code = emotion + distractors
                if code not in sum_dic:
                    sum_dic[code] = {}
                    counter_dic[code] = {}
                    mean_dic[code] = {}
                    sum_dic[code]['localization'] = 0
                    counter_dic[code]['localization'] = 0
                    sum_dic[code]['delay'] = 0
                    counter_dic[code]['delay'] = 0
                    sum_dic[code]['response_time'] = 0
                    counter_dic[code]['response_time'] = 0
                    mean_dic[code]['localization'] = None
                    mean_dic[code]['delay'] = None
                    mean_dic[code]['response_time'] = None
                if (error == '0' or error == 'CONG') and localization_time != 'None' and 'early capture' not in blink:
                    sum_dic[code]['localization'] += float(localization_time)
                    counter_dic[code]['localization'] += 1
                    sum_dic[code]['delay'] += float(response_delay)
                    counter_dic[code]['delay'] += 1
                    sum_dic[code]['response_time'] += float(response_time)
                    counter_dic[code]['response_time'] += 1

            for code in mean_dic:
                for key in mean_dic[code]:
                    if sum_dic[code][key] != 0:
                        mean_dic[code][key] = sum_dic[code][key]/counter_dic[code][key]

            for line in subject:
                emotion = line[5]
                distractors = line[7]
                error = line[14]
                response_time = line[15]
                localization_time = line[16]
                response_delay = line[17]
                blink = line[20]
                code = emotion + distractors
                if code not in SS_dic:
                    SS_dic[code] = {}
                    counter_SS_dic[code] = {}
                    SD_dic[code] = {}
                    SS_dic[code]['localization'] = 0
                    counter_SS_dic[code]['localization'] = 0
                    SS_dic[code]['delay'] = 0
                    counter_SS_dic[code]['delay'] = 0
                    SS_dic[code]['response_time'] = 0
                    counter_SS_dic[code]['response_time'] = 0
                    SD_dic[code]['localization'] = None
                    SD_dic[code]['delay'] = None
                    SD_dic[code]['response_time'] = None
                if (error == '0' or error == 'CONG') and localization_time != 'None' and 'early capture' not in blink:
                    SS_dic[code]['localization'] += squareSum(float(localization_time), mean_dic[code]['localization'])
                    counter_SS_dic[code]['localization'] += 1
                    SS_dic[code]['delay'] += squareSum(float(response_delay), mean_dic[code]['delay'])
                    counter_SS_dic[code]['delay'] += 1
                    SS_dic[code]['response_time'] += squareSum(float(response_time), mean_dic[code]['response_time'])
                    counter_SS_dic[code]['response_time'] += 1

                for code in SD_dic:
                    for key in SD_dic[code]:
                        if SS_dic[code][key] != 0:
                            SD_dic[code][key] = sqrt(SS_dic[code][key]/counter_SS_dic[code][key])

            for line in subject:
                subject_num = line[0]
                emotion = line[5]
                distractors = line[7]
                error = line[14]
                response_time = line[15]
                localization_time = line[16]
                response_delay = line[17]
                blink = line[20]
                code = emotion + distractors
                new_line = line
                for key in mean_dic[code]:
                    if key == 'localization':
                        score = localization_time
                    elif key == 'delay':
                        score = response_delay
                    elif key == 'response_time':
                        score = response_time
                    if SD_dic[code][key] != None and (error == '0' or error == 'CONG') and localization_time != 'None' and 'early capture' not in blink:
                        current_mean = mean_dic[code][key]
                        current_SD = SD_dic[code][key]
                        if (float(score) > (float(current_mean) + 3*float(current_SD)) or float(score) < (float(current_mean) - 3*float(current_SD))):
                                print(key, " in a ", emotion, distractors, " trial exceeds 3 SD for subject ", subject_num, " : ",
                                      str(score), ", mean: ", str(current_mean), ", SD: ", str(current_SD))
                                new_line.append("Deviant %s 3 SD" %key)
                        elif (float(score) > (float(current_mean) + 2*float(current_SD)) or float(score) < (float(current_mean) - 2*float(current_SD))):
                                print(key, " in a ", emotion, distractors, " trial exceeds 2 SD for subject ", subject_num, " : ",
                                      str(score), ", mean: ", str(current_mean), ", SD: ", str(current_SD))
                                new_line.append("Deviant %s 2 SD" %key)
                        else:
                            new_line.append("Normal %s value" %key)
                    else:
                        new_line.append("%s not relevant" %key)
                s = ";".join([str(e) for e in new_line]) + "\n"
                data_modified.write(s)
        data_modified.close()

    @staticmethod
    def getDefaultResultsFile():
        return joinPaths(getResultsFolder(), 'visual_search.csv')

    @staticmethod
    def makeResultFile() -> None:
        createResultsFolder()
        Visual_search.makeResultFile(getDefaultResultsFile)

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
    def plotTarget(region: RectangleRegion, cor_resp, color):
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
    def scanpath(self, subject_id, trial, frequency : int):
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
                Visual_search.plotTarget(frame, trial.features['cor_resp'], target_color)
            else:
                plotRegion(frame, frame_color)

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
        target_color = (1,0,0)
        point_color = (1,1,0)

        # Taking frequency into account
        point_list_f = []
        for i in range(0,len(point_list)-frequency,frequency):
            point_list_f.append(point_list[i])

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

            for frame in frame_list:
                if frame.isTarget((trial.features['target_hp'], trial.features['target_vp'])):
                    Visual_search.plotTarget(frame, trial.features['cor_resp'], target_color)
                else:
                    plotRegion(frame, frame_color)

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

    def parseSubject(self, input_file : str, progress = None) -> Subject:

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
