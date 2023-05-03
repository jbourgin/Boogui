import re #To format data lists
from eyetracking.experiment import *
from eyetracking.interest_region import *
from eyetracking.scanpath import *
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication

class Exp(Experiment):

    def __init__(self):
        super().__init__({'training', 'target_side'})
        self.n_trials = 96
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

    ###############################################
    ############## Overriden methods ##############
    ###############################################

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

    def parseStartTrial(self, line: List[str]) -> Union[Entry, None]:
        if len(line) >= 4 and line[2] == 'BEGIN' and line[3] == 'TRANSITION' and line[4] == 'time_transition':
            try:
                time = int(line[1])
                trial_number = int(line[-1])
                stimulus = line[10]
                return StartTrial(time, trial_number, stimulus)
            except:
                pass
        return None

    def isTraining(self, trial) -> bool:
        return 'App' in trial.features['training']

    def isResponse(self, line: Line) -> bool :
        return len(line) >= 5 and 'END' in line[2] and 'TRANSITION' in line[3] and 'TIMEOUT' in line[4]

    def parseStopTrial(self, line: List[str]) -> Union[Entry, None]:
        if len(line) >= 4 and line[2] == 'END' and line[3] == 'SEQUENCE':
            try:
                time = int(line[1])
                return StopTrial(time)
            except:
                pass
        return None

    ######################################################
    ############## End of Overriden methods ##############
    ######################################################

    def processTrial(self, subject: Subject, trial, filename = None):
        super().__init__(self, subject, trial)
        targetname = trial.getStimulus()

        if trial.saccades == []:
            logTrace ('Subject %i has no saccades at trial %i !' %(subject.id, trial.id), Precision.DETAIL)
        else:
            if trial.features['target_side'] == 'Gauche':
                correct_position = 'Left'
                target_position = self.left
            elif trial.features['target_side'] == 'Droite':
                correct_position = 'Right'
                target_position = self.right

            start_trial_time = trial.getStartTrial().getTime()

            if 'Neg' in targetname[:3]:
                emotion = 'Negative'
            elif 'P' in targetname[0]:
                emotion = 'Positive'
            elif 'Neu' in targetname[:3]:
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
            if not trial.isStartValid(self.screen_center, self.valid_distance_center)[0]:
                error = "No valid start"
            elif blink_category == 'early capture':
                error = "Early blink"
            elif SRT_real <= 80:
                error = "Anticipation saccade"
            elif sac_duration < 22:
                error = "Short saccade"
            elif sac_amplitude < self.valid_distance_center:
                error = "Micro saccade"
            elif ((correct_position == 'Right'
                  and horizontal_gaze_position_end < self.screen_center[0])
                  or (correct_position == 'Left'
                      and horizontal_gaze_position_end > self.screen_center[0])):
                error = '1'
            elif ((correct_position == 'Right'
                  and horizontal_gaze_position_end > self.screen_center[0])
                  or (correct_position == 'Left'
                      and horizontal_gaze_position_end < self.screen_center[0])):
                error = '0'
            else:
                error = None

            # Writing data in result csv file
            s = [str(subject.id) + '-E', # Subject name
                subject.group,
                trial.id,
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
                trial.saccades[0].getEndTime() - trial.saccades[0].getStartTime(),
                blink_category,
                threshold_excess]

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
            d['error'] = line[9]
            d['blink'] = line[14]
            try:
                d['saccade'] = float(line[10])
            except:
                d['saccade'] = line[10]
            try:
                d['duration'] = float(line[13])
            except:
                d['duration'] = line[13]
            return d

        # In the first version, only saccade durations with a duration higher than 100 ms could be considered as deviant.
        with open(filename) as datafile:
            data = datafile.read()
        data_modified = open(filename, 'w')
        data = data.split('\n')
        data = [x.split(';') for x in data]
        subject = "Subject"
        sequence = []
        data_seq = []
        list_scores = ['saccade', 'duration']

        for line in data:
            if line[0] == "Subject":
                new_line = line
                new_line.append('Saccade sorting')
                new_line.append('Duration sorting')
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
                pass
            elif group == "SAS" or group == "MA":
                pass
            else:
                raise ExperimentException('No appropriate group for subject %s' % subject[0][0])

            for line in subject:
                dic_variables = initialize_variables(line)
                code = dic_variables['emotion']
                if code not in elements_list:
                    elements_list[code] = {}
                    mean_dic[code] = {}
                    for element in list_scores:
                        elements_list[code][element] = []
                        mean_dic[code][element] = None
                if dic_variables['error'] == '0' and dic_variables['saccade'] != 'None' and "early" not in dic_variables['blink']:
                    elements_list[code]['saccade'].append(dic_variables['saccade'])
                    elements_list[code]['duration'].append(dic_variables['duration'])

            for code in mean_dic:
                for key in mean_dic[code]:
                    if len(elements_list[code][key]) != 0:
                        mean_dic[code][key] = sum(elements_list[code][key])/len(elements_list[code][key])

            for line in subject:
                dic_variables = initialize_variables(line)
                code = dic_variables['emotion']
                if code not in square_dic:
                    square_dic[code] = {}
                    SD_dic[code] = {}
                    for element in list_scores:
                        square_dic[code][element] = []
                        SD_dic[code][element] = None
                if dic_variables['error'] == "0" and dic_variables['saccade'] != "None" and "early" not in dic_variables['blink']:
                    square_dic[code]['saccade'].append(squareSum(dic_variables['saccade'], mean_dic[code]['saccade']))
                    square_dic[code]['duration'].append(squareSum(dic_variables['duration'], mean_dic[code]['duration']))

                for code in SD_dic:
                    for key in SD_dic[code]:
                        if len(square_dic[code][key]) != 0:
                            if len(square_dic[code][key]) > 1:
                                SD_dic[code][key] = sqrt(sum(square_dic[code][key])/(len(square_dic[code][key])-1))
                            else:
                                SD_dic[code][key] = sqrt(sum(square_dic[code][key])/len(square_dic[code][key]))

            for line in subject:
                dic_variables = initialize_variables(line)
                code = dic_variables['emotion']
                new_line = line
                for key in mean_dic[code]:
                    if key == 'saccade':
                        score = dic_variables['saccade']
                    elif key == 'duration':
                        score = dic_variables['duration']
                    if SD_dic[code][key] != None and dic_variables['error'] == "0" and dic_variables['saccade'] != "None" and "early" not in dic_variables['blink']:
                        current_mean = mean_dic[code][key]
                        current_SD = SD_dic[code][key]
                        if (float(score) > (float(current_mean) + 3*float(current_SD)) or float(score) < (float(current_mean) - 3*float(current_SD))):
                                print(key, " in a ", code, " trial exceeds 3 SD for subject ", dic_variables['subject_num'], " : ",
                                      str(score), ", mean: ", str(current_mean), ", SD: ", str(current_SD))
                                new_line.append("Deviant %s 3 SD" %key)
                        elif (float(score) > (float(current_mean) + 2*float(current_SD)) or float(score) < (float(current_mean) - 2*float(current_SD))):
                                print(key, " in a ", code, " trial exceeds 2 SD for subject ", dic_variables['subject_num'], " : ",
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
            'First saccade duration',
            'First blink type',
            'Threshold excess'
        ]))
        f.write('\n')
        f.close()

    # Creates an image scanpath for one trial.
    def scanpath(self, subject: Subject, trial, frequency : int):
        plt.clf()

        if 'P' in trial.getStimulus()[0]:
            frame_color = (0,1,0)
        elif 'Neg' in trial.getStimulus()[:3]:
            frame_color = (1,0,0)
        else:
            frame_color = (0,0,0)

        x_axis = self.screen_center[0] * 2
        y_axis = self.screen_center[1] * 2
        plt.axis([0, x_axis, 0, y_axis])
        plt.gca().invert_yaxis()
        plt.axis('off')

        # Plotting frames
        if trial.features['target_side'] == 'Gauche':
            plotRegion(self.left, frame_color)
        elif trial.features['target_side'] == 'Droite':
            plotRegion(self.right, frame_color)

        # Plotting gaze positions
        trial.plot(frequency)
        image_name = 'subject_%i_trial_%i.png' % (subject.id, trial.id)
        saveImage(getTmpFolder(), image_name)
        return image_name

    # Creates a video scanpath for one trial.
    def scanpathVideo(self, subject: Subject, trial, frequency : int, progress = None):
        n_elem_drawn = 20
        point_list = trial.getGazePoints()
        nb_points = len(point_list)
        point_color = (1,1,0)

        if 'P' in trial.getStimulus()[0]:
            frame_color = (0,1,0)
        elif 'Neg' in trial.getStimulus()[:3]:
            frame_color = (1,0,0)
        else:
            frame_color = (0,0,0)

        # Taking frequency into account
        point_list_f = []
        for i in range(0,len(point_list)-frequency,frequency):
            point_list_f.append(point_list[i])

        image_list = []

        axis_x = self.screen_center[0]*2
        axis_y = self.screen_center[1]*2

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
                plotRegion(self.left, frame_color)
            elif trial.features['target_side'] == 'Droite':
                plotRegion(self.right, frame_color)

            image_name = '%i.png' % elem
            saveImage(getTmpFolder(), image_name)
            image_list.append(joinPaths(getTmpFolder(), image_name))
        vid_name = 'subject_%i_trial_%s.avi' % (subject.id, trial.id)
        progress.setText(0, 'Loading frames')
        makeVideo(image_list, vid_name, fps=100/frequency)
        return vid_name

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
