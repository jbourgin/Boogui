from eyetracking.experiment import *
from eyetracking.interest_region import *
import pandas as pd
from PyQt5.QtWidgets import QApplication

class PSCol(Col):

    # Specific columns
    EMOTION = "Emotion"
    TARGET = "Target Name"
    SIDE = "Target Side"
    COR_POS = "Correct position"
    ERR = "Errors"
    FIRST_RT = "First saccade RT"
    FIRST_POS_START = "First saccade start gaze position"
    FIRST_POS_END = "First saccade ending gaze position"
    FIRST_DUR = "First saccade duration"
    THRESH = "Threshold excess"
    TRAINING = "Training"

class Exp(Experiment):

    def __init__(self):
        super().__init__({'training', 'target_side'}, __file__)
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

    def processTrial(self, subject: Subject, trial):
        super().processTrial(subject, trial)
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
            new_dict = {
                PSCol.TRAINING: trial.features['training'],
                PSCol.EMOTION: emotion,
                PSCol.TARGET: targetname,
                PSCol.SIDE: trial.features['target_side'],
                PSCol.COR_POS: correct_position,
                PSCol.ERR: error,
                PSCol.FIRST_RT: trial.saccades[0].getStartTime() - start_trial_time,
                PSCol.FIRST_POS_START: trial.saccades[0].getFirstGazePosition(),
                PSCol.FIRST_POS_END: trial.saccades[0].getLastGazePosition(),
                PSCol.FIRST_DUR: trial.saccades[0].getEndTime() - trial.saccades[0].getStartTime(),
                PSCol.BLINK: blink_category,
                PSCol.THRESH: threshold_excess
            }
            self.trial_dict.update(new_dict)

            df = pd.DataFrame([self.trial_dict])
            if self.dataframe is None:
                self.dataframe = df
            else:
                self.dataframe = pd.concat([self.dataframe, df])

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

    # Get frame color (stim delimitation during scanpath plot)
    def getFrameColor(self, trial):
        if 'P' in trial.getStimulus()[0]:
            return (0,1,0)
        elif 'Neg' in trial.getStimulus()[:3]:
            return (1,0,0)
        return (0,0,0)

    # plot regions for image scanpath
    def plotRegions(self, trial):
        frame_color = self.getFrameColor(trial)
        if trial.features['target_side'] == 'Gauche':
            plotRegion(self.left, frame_color)
        elif trial.features['target_side'] == 'Droite':
            plotRegion(self.right, frame_color)
