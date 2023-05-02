import re #To format data lists
from eyetracking.experiment import *
from eyetracking.interest_region import *
from eyetracking.scanpath import *
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PyQt5.QtWidgets import QApplication
import sys
import random
import numpy as np

class Exp(Experiment):

    def __init__(self):
        super().__init__({'target_hp', 'target_vp', 'num_of_dis', 'cor_resp', 'response', 'target_side'})
        self.n_trials = 120

        # Center of the screen.
        self.screen_center = (512,384)
        # Minimal distance at which we consider the subject is looking at the
        # fixation cross at the trial beginning
        self.valid_distance_center = 95 #3 degres of visual angle 95

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

    ###############################################
    ############## Overriden methods ##############
    ###############################################

    # Returns a dictionary of experiment variables
    def parseVariables(self, line: List[str]):
        if len(line) > 24 and line[8] == "tgt_hor":
            try:
                if len(line) > 24 and line[8] == "tgt_hor":
                    target_hp = int(line[10]) + self.screen_center[0]
                    target_vp = int(line[15]) + self.screen_center[1]
                    num_of_dis = int(line[5])
                    cor_resp = line[20]
                    response = line[24]
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

    ######################################################
    ############## End of Overriden methods ##############
    ######################################################

    def processTrial(self, subject: Subject, trial, filename = None):
        logTrace ('Processing trial n°%i' % trial.id, Precision.DETAIL)

        if trial.saccades == []:
            logTrace ("Subject %i has no saccades at trial %i !" %(subject.id,trial.id), Precision.DETAIL)

        if trial.features['num_of_dis'] == 1:
            frame_list = self.frame_list_1
        elif trial.features['num_of_dis'] == 3:
            frame_list = self.frame_list_3
        elif trial.features['num_of_dis'] == 5:
            frame_list = self.frame_list_5

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
        if trial.id < 60 and target_cat != "VISAGE":
            block = 1
        elif trial.id >= 60:
            block = 2

        #We determine congruency between target side and frame break side.
        congruency = None
        if ((trial.features['target_hp'] < self.screen_center[0] and trial.features['cor_resp'] == '1')
        or (trial.features['target_hp'] > self.screen_center[0] and trial.features['cor_resp'] == '2')):
            congruency = "YES"
        else:
            congruency = "NO"

        # First and last good fixations
        try:
            first_good_fixation = next(fixation for fixation in region_fixations if fixation.on_target)
            last_good_fixation = next(fixation for fixation in reversed(region_fixations) if fixation.on_target)
            response_delay_last = response_time - (last_good_fixation.getStartTimeFromStartTrial())
            # Delay of capture to the first good fixation
            capture_delay_first = first_good_fixation.getStartTimeFromStartTrial()
        except:
            first_good_fixation = None
            last_good_fixation = None
            response_delay_last = None
            capture_delay_first = None
        try:
            last_fixation = region_fixations[-1].on_target
        except:
            last_fixation = None

        # Time on target and distractors
        total_target_fixation_time = sum(x.duration() for x in region_fixations if x.on_target)
        if total_target_fixation_time == 0:
            total_target_fixation_time = None
        total_distractor_fixation_time = sum(x.duration() for x in region_fixations if not x.on_target)
        if total_distractor_fixation_time == 0:
            total_distractor_fixation_time = None

        # Determining blink category
        if trial.blinks == []:
            blink_category = "No blink"
        else:
            if first_good_fixation != None and trial.blinks[0].getStartTime() < first_good_fixation.getStartTime():
                blink_category = "early capture"
            else:
                blink_category = "late"

        # Error :
        if not trial.isStartValid(self.screen_center, self.valid_distance_center)[0]:
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
            and subject in self.list_patients_cong
            and congruency == "NO"
            and trial.features['cor_resp'] != trial.features['response']):
            error = 'CONG'
        else:
            if trial.features['cor_resp'] != trial.features['response']:
                error = '1'
            else:
                error = '0'

        # Writing data in result csv file
        subject_name = str(subject.id) + "-E"
        s = [subject_name, # Subject name
            subject.group,
            trial.id,
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
            blink_category,
            last_fixation]

        if filename is None:
            f = open(getResultsFile(), 'a')
        else:
            f = open(filename, 'a')
        f.write(';'.join([str(x) for x in s]))
        f.write('\n')
        f.close()

    def postProcess(self, filename: str):
        def initialize_variables(line):
            d = dict()
            d['subject_num'] = line[0]
            d['emotion'] = line[5]
            d['trialid'] = line[2]
            d['distractors'] = line[7]
            d['error'] = line[14]
            try:
                d['response_time'] = float(line[15])
            except:
                d['response_time'] = line[15]
            try:
                d['localization_time'] = float(line[16])
            except:
                d['localization_time'] = line[16]
            try:
                d['response_delay'] = float(line[17])
            except:
                d['response_delay'] = line[17]
            d['blink'] = line[20]
            d['last_fixation'] = line[21]
            return d

        with open(filename) as datafile:
            data = datafile.read()
        data_modified = open(filename, 'w')
        data = data.split('\n')
        data = [x.split(';') for x in data]
        subject = "Subject"
        sequence = []
        data_seq = []
        capture_threshold = 100
        low_threshold_delay_young = 360
        low_threshold_delay_old = 560
        list_scores = ['localization', 'delay', 'response_time']

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
            elements_list = {}
            mean_dic = {}
            square_dic = {}
            SD_dic = {}
            group = subject[0][1]
            if group == "SJS":
                low_threshold_delay = low_threshold_delay_young
            elif group == "SAS" or group == "MA":
                low_threshold_delay = low_threshold_delay_old
            else:
                raise ExperimentException('No appropriate group for subject %s' % subject[0][0])

            for line in subject:
                dic_variables = initialize_variables(line)
                code = dic_variables['emotion'] + dic_variables['distractors']
                if code not in elements_list:
                    elements_list[code] = {}
                    mean_dic[code] = {}
                    for element in list_scores:
                        elements_list[code][element] = []
                        mean_dic[code][element] = None
                if (dic_variables['error'] == '0' or dic_variables['error'] == 'CONG') and dic_variables['localization_time'] != 'None' and dic_variables['localization_time'] >= capture_threshold:
                    elements_list[code]['localization'].append(dic_variables['localization_time'])
                    if float(dic_variables['response_delay']) > low_threshold_delay and dic_variables['error'] == '0' and dic_variables['last_fixation'] == 'True':
                        elements_list[code]['delay'].append(dic_variables['response_delay'])
                    elements_list[code]['response_time'].append(dic_variables['response_time'])

            for code in mean_dic:
                for key in mean_dic[code]:
                    if len(elements_list[code][key]) != 0:
                        mean_dic[code][key] = sum(elements_list[code][key])/len(elements_list[code][key])

            for line in subject:
                dic_variables = initialize_variables(line)
                code = dic_variables['emotion'] + dic_variables['distractors']
                if code not in square_dic:
                    square_dic[code] = {}
                    SD_dic[code] = {}
                    for element in list_scores:
                        square_dic[code][element] = []
                        SD_dic[code][element] = None
                if (dic_variables['error'] == '0' or dic_variables['error'] == 'CONG') and dic_variables['localization_time'] != 'None' and dic_variables['localization_time'] >= capture_threshold:
                    square_dic[code]['localization'].append(squareSum(dic_variables['localization_time'], mean_dic[code]['localization']))
                    if float(dic_variables['response_delay']) > low_threshold_delay and dic_variables['error'] == '0' and dic_variables['last_fixation'] == "True":
                        square_dic[code]['delay'].append(squareSum(dic_variables['response_delay'], mean_dic[code]['delay']))
                    square_dic[code]['response_time'].append(squareSum(dic_variables['response_time'], mean_dic[code]['response_time']))

                for code in SD_dic:
                    for key in SD_dic[code]:
                        if len(square_dic[code][key]) != 0:
                            if len(square_dic[code][key]) > 1:
                                SD_dic[code][key] = sqrt(sum(square_dic[code][key])/(len(square_dic[code][key])-1))
                            else:
                                SD_dic[code][key] = sqrt(sum(square_dic[code][key])/len(square_dic[code][key]))

            for line in subject:
                dic_variables = initialize_variables(line)
                code = dic_variables['emotion'] + dic_variables['distractors']
                new_line = line
                for key in mean_dic[code]:
                    if key == 'localization':
                        score = dic_variables['localization_time']
                    elif key == 'delay':
                        score = dic_variables['response_delay']
                    elif key == 'response_time':
                        score = dic_variables['response_time']
                    if key == 'delay' and score != "None" and float(score) <= low_threshold_delay and dic_variables['error'] == '0':
                        new_line.append("Deviant response delay")
                    elif SD_dic[code][key] != None and (dic_variables['error'] == '0' or dic_variables['error'] == 'CONG') and dic_variables['localization_time'] != 'None' and dic_variables['localization_time'] >= capture_threshold:
                        if key == 'delay' and (dic_variables['error'] == 'CONG' or dic_variables['last_fixation'] != 'True'):
                            new_line.append("%s not relevant" %key)
                        else:
                            current_mean = mean_dic[code][key]
                            current_SD = SD_dic[code][key]
                            if (score > (current_mean + 3*current_SD) or score < ((current_mean) - 3*current_SD)):
                                    print(key, " in a ", dic_variables['emotion'], dic_variables['distractors'], " trial %s " % dic_variables['trialid'],
                                          "exceeds 3 SD for subject ", dic_variables['subject_num'], " : ",
                                          str(score), ", mean: ", str(current_mean), ", SD: ", str(current_SD))
                                    new_line.append("Deviant %s 3 SD" %key)
                            elif (score > (current_mean + 2*current_SD) or score < (current_mean - 2*current_SD)):
                                    print(key, " in a ", dic_variables['emotion'], dic_variables['distractors'], " trial %s " % dic_variables['trialid'],
                                          "exceeds 2 SD for subject ", dic_variables['subject_num'], " : ",
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
        Exp.makeResultFile(getDefaultResultsFile)

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
            'First blink type',
            'Last fixation type'
        ]))
        f.write('\n')
        f.close()

    @staticmethod
    def plotTarget(region: RectangleRegion, cor_resp, color):
    	lu_corner = [region.center[0]-region.half_width, region.center[1]+region.half_height]
    	lb_corner = [region.center[0]-region.half_width, region.center[1]-region.half_height]
    	ru_corner = [region.center[0]+region.half_width, region.center[1]+region.half_height]
    	rb_corner = [region.center[0]+region.half_width, region.center[1]-region.half_height]

    	if cor_resp == '2':
    		hole_up = [region.center[0]+region.half_width, region.center[1]+30]
    		hole_down = [region.center[0]+region.half_width, region.center[1]-30]
    		plotSegment(lu_corner, lb_corner, c=color)
    		plotSegment(lb_corner, rb_corner, c=color)
    		plotSegment(rb_corner, hole_down, c=color)
    		plotSegment(hole_up, ru_corner, c=color)
    		plotSegment(ru_corner, lu_corner, c=color)

    	elif cor_resp == '1':
    		hole_up = [region.center[0]-region.half_width, region.center[1]+30]
    		hole_down = [region.center[0]-region.half_width, region.center[1]-30]
    		plotSegment(lb_corner, rb_corner, c=color)
    		plotSegment(rb_corner, ru_corner, c=color)
    		plotSegment(ru_corner, lu_corner, c=color)
    		plotSegment(lb_corner, hole_down, c=color)
    		plotSegment(hole_up, lu_corner, c=color)

    # Creates an image scanpath for one trial.
    def scanpath(self, subject: Subject, trial, frequency : int):
        plt.clf()

        frame_color = (0,0,0)
        target_color = (1,0,0)
        x_axis = self.screen_center[0] * 2
        y_axis = self.screen_center[1] * 2
        plt.axis([0, x_axis, 0, y_axis])
        plt.gca().invert_yaxis()
        plt.axis('off')

        # Plotting image
        folder_image = 'D:\\Visualsearch\\'
        image_name = os.path.join(
            folder_image,
            trial.getStimulus().split("\\")[-1].split('.')[0] + '.png'
        )
        image = None
        listneutral = []

        if os.path.isfile(image_name):
            image = mpimg.imread(image_name, format = 'png')
            for file in os.listdir(folder_image):
                if file.startswith('neu'):
                    listneutral.append(os.path.join(folder_image, file))

        # Plotting frames
        if trial.features['num_of_dis'] == 1:
            frame_list = self.frame_list_1.getRegions()
        elif trial.features['num_of_dis'] == 3:
            frame_list = self.frame_list_3.getRegions()
        elif trial.features['num_of_dis'] == 5:
            frame_list = self.frame_list_5.getRegions()

        for frame in frame_list:
            if frame.isTarget((trial.features['target_hp'], trial.features['target_vp'])):
                if image is not None:
                    plt.imshow(image, cmap = plt.get_cmap('gray'), extent=[
                        frame.center[0] - frame.half_width,
                        frame.center[0] + frame.half_width,
                        frame.center[1] + frame.half_height,
                        frame.center[1] - frame.half_height
                    ])
                Exp.plotTarget(frame, trial.features['cor_resp'], target_color)
            else:
                plotRegion(frame, frame_color)
                if image is not None:
                    neutral_stim = random.choice(listneutral)
                    neutral_img = mpimg.imread(neutral_stim, format = 'png')
                    listneutral.remove(neutral_stim)
                    plt.imshow(neutral_img, cmap = plt.get_cmap('gray'), extent=[
                        frame.center[0] - frame.half_width,
                        frame.center[0] + frame.half_width,
                        frame.center[1] + frame.half_height,
                        frame.center[1] - frame.half_height
                    ])

        # Plotting gaze positions
        trial.plot(frequency)
        if trial.isTraining():
            image_name = 'subject_%i_training_%i.png' % (subject.id, trial.id)
        else:
            image_name = 'subject_%i_trial_%i.png' % (subject.id, trial.id)
        saveImage(getTmpFolder(), image_name)
        return image_name

    # Creates a video scanpath for one trial.
    def scanpathVideo(self, subject: Subject, trial, frequency : int, progress = None):
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

        # Plotting image
        folder_image = 'D:\\Visualsearch\\'
        image_name = os.path.join(
            folder_image,
            trial.getStimulus().split("\\")[-1].split('.')[0] + '.png'
        )
        image = None
        listneutral = []

        if os.path.isfile(image_name):
            image = mpimg.imread(image_name, format = 'png')
            for file in os.listdir(folder_image):
                if file.startswith('neu'):
                    listneutral.append(os.path.join(folder_image, file))

        image_list = []
        # Plotting frames
        if trial.features['num_of_dis'] == 1:
            frame_list = self.frame_list_1.getRegions()
        elif trial.features['num_of_dis'] == 3:
            frame_list = self.frame_list_3.getRegions()
        elif trial.features['num_of_dis'] == 5:
            frame_list = self.frame_list_5.getRegions()

        axis_x = self.screen_center[0]*2
        axis_y = self.screen_center[1]*2

        logTrace ('Creating video frames', Precision.NORMAL)

        if progress != None:
            progress.setText(0, 'Loading frames')
            progress.setMaximum(0, len(point_list_f) - 1)

        if image is not None:
            final_listneutral = []
            for frame_dis in range(len(frame_list)-1):
                neutral_stim = random.choice(listneutral)
                listneutral.remove(neutral_stim)
                final_listneutral.append(neutral_stim)

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

            count_neutral = 0
            for frame in frame_list:
                if frame.isTarget((trial.features['target_hp'], trial.features['target_vp'])):
                    if image is not None:
                        plt.imshow(image, cmap = plt.get_cmap('gray'), extent=[
                            frame.center[0] - frame.half_width,
                            frame.center[0] + frame.half_width,
                            frame.center[1] + frame.half_height,
                            frame.center[1] - frame.half_height
                        ])
                    Exp.plotTarget(frame, trial.features['cor_resp'], target_color)
                else:
                    plotRegion(frame, frame_color)
                    if image is not None:
                        neutral_img = mpimg.imread(final_listneutral[count_neutral], format = 'png')
                        count_neutral += 1
                        plt.imshow(neutral_img, cmap = plt.get_cmap('gray'), extent=[
                        frame.center[0] - frame.half_width,
                        frame.center[0] + frame.half_width,
                        frame.center[1] + frame.half_height,
                        frame.center[1] - frame.half_height
                    ])

            image_name = '%i.png' % elem
            saveImage(getTmpFolder(), image_name)
            image_list.append(joinPaths(getTmpFolder(), image_name))
        if trial.isTraining():
            vid_name = 'subject_%i_training_%s.avi' % (subject.id, trial.id)
        else:
            vid_name = 'subject_%i_trial_%s.avi' % (subject.id, trial.id)

        progress.setText(0, 'Loading frames')
        makeVideo(image_list, vid_name, fps=100/frequency)
        return vid_name

    def getSubjectData(self, line: str) -> Union[Tuple[int,str]]:
        try:
            l = re.split("[\t ]+", line)
            return (int(l[1]), l[2])
        except:
            return None

    default_subject_id = 1
    default_category = 'Not defined'
    #default_category = 'SAS'

    def parseSubject(self, input_file : str, progress = None) -> Subject:

        with open(input_file) as f:
            first_line = f.readline()
            if first_line[-1] == '\n':
                first_line = first_line[:-1]

        subject_data = self.getSubjectData(first_line)

        if subject_data is None:
            logTrace ('Subject number and category could not be found', Precision.ERROR)
            subject_data = (Exp.default_subject_id, Exp.default_category)
            Exp.default_subject_id += 1

        result_file = "results.txt"
        datafile = open(input_file, "r")

        #File conversion in list.
        data = datafile.read()
        data = list(data.splitlines())

        #We add a tabulation and space separator.
        data = [re.split("[\t ]+",line) for line in data]

        (n_subject, subject_cat) = subject_data
        return Subject(self, self.n_trials, data, n_subject, subject_cat, progress)
