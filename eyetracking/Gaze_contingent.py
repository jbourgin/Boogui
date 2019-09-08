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
        self.screen_center = (683,384)
        # Minimal distance at which we consider the subject is looking at the
        # fixation cross at the trial beginning
        self.valid_distance_center = 100 #3 degres of visual angle 95 (+ marge)

        # Initializing regions of interest
        self.half_width = 200 #200
        self.half_height_face = 268 #268
        self.half_height_eye = 45 #45

        # frames
        self.right_gaze = RectangleRegion((self.screen_center[0]*(1+1/3), self.screen_center[1]+10), self.half_width, self.half_height_eye)
        self.left_gaze = RectangleRegion((self.screen_center[0]-(self.screen_center[0]/3), self.screen_center[1]+10), self.half_width, self.half_height_eye)
        self.right_ellipse = EllipseRegion((self.screen_center[0]*(1+1/3), self.screen_center[1]), self.half_width, self.half_height_face)
        self.left_ellipse = EllipseRegion((self.screen_center[0]-(self.screen_center[0]/3), self.screen_center[1]), self.half_width, self.half_height_face)
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
                    cor_resp = line[11]
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

    def parseMessage(self, line: List[str]):
        if len(line) > 6 and line[4] == "showing":
            try:
                time = int(line[1])
                message = 'End image showing'
                return Entry.Message(time, message)
            except:
                pass
        return None

    def isResponse(self, line: Line) -> bool :
        return len(line) >= 5 and 'responded' in line[4]

    def isTraining(self, trial) -> bool:
        return 'Training' in trial.features['training']

class Gaze_contingent(Experiment):

    def __init__(self):
        super().__init__(None)
        self.n_trials = 96
        self.expected_features = {'training', 'session', 'global_task', 'emotion', 'gender', 'target_side', 'response', 'cor_resp', 'response_time'}

    def selectEyetracker(self, input_file : str) -> None:
        logTrace ('Selecting Eyelink', Precision.NORMAL)
        self.eyetracker = Make_Eyelink()

    def returnStopImageEntry(self, trial) -> int:
        @match(Entry)
        class checkMessage(object):
            def Message(time, message):
                return 'End image showing' in message
            def _(_):
                return False

        for count, entry in enumerate(trial.entries):
            if checkMessage(entry):
                return count
        return None

    def recalibrate(self, subject : Subject) -> None:
        def shift(trial, vec):
            for (i_entry,entry) in enumerate(trial.entries):
                pos = getGazePosition(entry)
                if pos != None:
                    trial.entries[i_entry] = Entry.Position(
                        getTime(entry),
                        pos[0] + vec[0],
                        pos[1] + vec[1]
                    )
        gaze_positions = []
        for (n_trial, trial) in enumerate(subject.trials):
            for fixation in trial.fixations:
                gaze_positions += [
                    getGazePosition(fixation.getEntry(i))
                    for i in range(fixation.getBegin(), fixation.getEnd())
                    if getGazePosition(fixation.getEntry(i)) != None
                ]

            if (n_trial + 1) % 24 == 0:
                gaze_positions = sorted(gaze_positions,
                    key = lambda x: x[1])
                # Removing first 5%
                id = int(len(gaze_positions)*5.0/100.0)
                print(id)
                gaze_positions = gaze_positions[id:]
                min_y = gaze_positions[0][1]
                print('min_y: ' + str(min_y))
                print(self.eyetracker.left_gaze)
                shift_y = self.eyetracker.left_gaze.center[1] - min_y
                for trial in subject.trials[n_trial - 23: n_trial+1]:
                    shift(trial, (0,shift_y))
                gaze_positions = []

    def processTrial(self, subject, trial, filename = None):
        logTrace ('Processing trial n°%i' % trial.getTrialId(), Precision.DETAIL)
        trial_number = trial.getTrialId()
        print("Subject %i, trial %i" %(subject.id,trial_number))
        print("eyetracker")
        print(self.eyetracker)
        #if len(line) >= 5 and 'response' in line[3] and 'screen' in line[4]:

        if trial.saccades == []:
            logTrace ("Subject %i has no saccades at trial %i !" %(subject.id,trial_number), Precision.DETAIL)

        if trial.features['target_side'] == 'Left':
            eye_position = self.eyetracker.left_gaze
            face_position = self.eyetracker.left_face
            start_point = (self.eyetracker.screen_center[0]*(1+1/3), self.eyetracker.screen_center[1]+150)
        elif trial.features['target_side'] == 'Right':
            eye_position = self.eyetracker.right_gaze
            face_position = self.eyetracker.right_face
            start_point = (self.eyetracker.screen_center[0]-(self.eyetracker.screen_center[0]/3), self.eyetracker.screen_center[1]+150)
        regions = InterestRegionList([eye_position, face_position])

        start_trial_time = trial.getStartTrial().getTime()

        targetname = trial.getStimulus()
        targetname = targetname.split('.')[0]

        end_line = self.returnStopImageEntry(trial)

        response_entry = trial.getResponse()

        region_fixations = trial.getFixationTime(regions, eye_position, end_line)

        # First and last good fixations
        try:
            first_good_fixation = next(fixation for fixation in region_fixations if fixation['target'])
            capture_delay_first = first_good_fixation['begin'].getTime() - start_trial_time
        except:
            first_good_fixation = None
            capture_delay_first = None

        # Time on target and distractors
        total_eye_fixation_time = sum(x['time'] for x in region_fixations if x['target'])
        # if total_eye_fixation_time == 0:
        #     total_eye_fixation_time = None
        total_faceNotEye_fixation_time = sum(x['time'] for x in region_fixations if not x['target'])
        total_fixation_time = total_eye_fixation_time + total_faceNotEye_fixation_time
        if total_fixation_time != 0:
            percent_eye = total_eye_fixation_time/total_fixation_time*100
            percent_face = total_faceNotEye_fixation_time/total_fixation_time*100
        else:
            percent_eye = None
            percent_face = None
        # if total_faceNotEye_fixation_time == 0:
        #     total_faceNotEye_fixation_time = None

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

        # if not trial.isStartValid(start_point, self.eyetracker.valid_distance_center)[0]:
        #     error = "Not valid start"
        if trial.features['response'] == 'None':
            error = "No subject response"
        elif total_fixation_time < 2000:
            error = "Low fixation time"
        elif blink_category == 'early capture':
            error = "Early blink"
        else:
            if trial.features['cor_resp'] != trial.features['response']:
                error = '1'
            else:
                error = '0'

        # Writing data in result csv file
        s = [str(subject.id) + "-E", # Subject name
            subject.group,
            trial_number,
            trial.features['session'],
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
            trial.isStartValid(start_point, self.eyetracker.valid_distance_center)[1],
            capture_delay_first,
            total_eye_fixation_time,
            total_faceNotEye_fixation_time,
            percent_eye,
            percent_face,
            blink_category]

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
            d['emotion'] = line[7]
            d['task'] = line[5]
            d['blink'] = line[19]
            d['error'] = line[13]
            try:
                d['response_time'] = float(line[14])
            except:
                d['response_time'] = line[14]
            try:
                d['first_eyes'] = float(line[16])
            except:
                d['first_eyes'] = line[16]
            return d

        with open(filename) as datafile:
            data = datafile.read()
        data_modified = open(filename, 'w')
        data = data.split('\n')
        data = [x.split(';') for x in data]
        subject = "Subject"
        sequence = []
        data_seq = []
        list_scores = ['first_eyes', 'response_time']

        for line in data:
            if line[0] == "Subject":
                new_line = line
                new_line.append('First time on eyes')
                new_line.append('Response time')
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
            if group == "YA":
                pass
            elif group == "SAS" or group == "MA":
                pass
            else:
                raise ExperimentException('No appropriate group for subject %s' % subject[0][0])

            for line in subject:
                dic_variables = initialize_variables(line)
                code = dic_variables['task'] + dic_variables['emotion']
                if code not in elements_list:
                    elements_list[code] = {}
                    mean_dic[code] = {}
                    for element in list_scores:
                        elements_list[code][element] = []
                        mean_dic[code][element] = None
                if dic_variables['first_eyes'] != 'None' and "early" not in dic_variables['blink']:
                    elements_list[code]['first_eyes'].append(dic_variables['first_eyes'])
                if dic_variables['response_time'] != 'None' and "early" not in dic_variables['blink']:
                    elements_list[code]['response_time'].append(dic_variables['response_time'])

            for code in mean_dic:
                for key in mean_dic[code]:
                    if len(elements_list[code][key]) != 0:
                        mean_dic[code][key] = sum(elements_list[code][key])/len(elements_list[code][key])

            for line in subject:
                dic_variables = initialize_variables(line)
                code = dic_variables['task'] + dic_variables['emotion']
                if code not in square_dic:
                    square_dic[code] = {}
                    SD_dic[code] = {}
                    for element in list_scores:
                        square_dic[code][element] = []
                        SD_dic[code][element] = None
                if dic_variables['first_eyes'] != 'None' and "early" not in dic_variables['blink']:
                    square_dic[code]['first_eyes'].append(squareSum(dic_variables['first_eyes'], mean_dic[code]['first_eyes']))
                if dic_variables['response_time'] != 'None' and "early" not in dic_variables['blink']:
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
                code = dic_variables['task'] + dic_variables['emotion']
                new_line = line
                for key in mean_dic[code]:
                    if key == 'first_eyes':
                        score = dic_variables['first_eyes']
                    elif key == 'response_time':
                        score = dic_variables['response_time']
                    print(key)
                    print(score)
                    if SD_dic[code][key] != None and dic_variables['error'] == "0" and score != "None" and score != "" and "early" not in dic_variables['blink']:
                        current_mean = mean_dic[code][key]
                        current_SD = SD_dic[code][key]
                        if (float(score) > (float(current_mean) + 3*float(current_SD)) or float(score) < (float(current_mean) - 3*float(current_SD))):
                                print(key, " in a ", dic_variables['emotion'], " trial exceeds 3 SD for subject ", dic_variables['subject_num'], " : ",
                                      str(score), ", mean: ", str(current_mean), ", SD: ", str(current_SD))
                                new_line.append("Deviant %s 3 SD" %key)
                        elif (float(score) > (float(current_mean) + 2*float(current_SD)) or float(score) < (float(current_mean) - 2*float(current_SD))):
                                print(key, " in a ", dic_variables['emotion'], " trial exceeds 2 SD for subject ", dic_variables['subject_num'], " : ",
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
            'Session',
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
            'First gaze position',
            'First time on eyes',
            'Total fixation time on eyes',
            'Total fixation time on face (other than eyes)',
            'Percent time on eyes',
            'Percent time on face',
            'First blink type',
        ]))
        f.write('\n')
        f.close()


    # Creates an image scanpath for one trial.
    def scanpath(self, subject_id, trial, frequency : int):
        plt.clf()

        end_line = self.returnStopImageEntry(trial)

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
        trial.plot(frequency, end_line)
        if trial.isTraining():
            image_name = 'subject_%i_training_%i.png' % (subject_id, trial.getTrialId())
        else:
            image_name = 'subject_%i_trial_%i.png' % (subject_id, trial.getTrialId())
        saveImage(getTmpFolder(), image_name)
        return image_name

    # Creates a video scanpath for one trial.
    def scanpathVideo(self, subject_id, trial, frequency : int, progress = None):
        n_elem_drawn = 20
        end_line = self.returnStopImageEntry(trial)
        point_list = trial.getGazePoints(end_line)
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
