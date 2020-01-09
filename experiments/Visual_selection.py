import re #To format data lists
from eyetracking.eyelink import *
from eyetracking.smi import *
from eyetracking.experiment import *
from eyetracking.interest_region import *
from eyetracking.scanpath import *
import matplotlib.pyplot as plt
import scipy.optimize
import scipy.interpolate
import scipy.integrate
import numpy
from PyQt5.QtWidgets import QApplication

class Make_Eyelink(Eyelink):
    def __init__(self):
        super().__init__()
        # Minimal distance at which we consider the subject is looking at the
        # fixation cross at the trial beginning
        self.valid_distance_center = 100 #3 degres of visual angle 95 (+ marge)

        # Initializing regions of interest
        self.half_width = 200 #200
        self.half_height = 200 #150

        self.setupStandard()


    def setupStandard(self):
        # Center of the screen.
        self.screen_center = (640,400)

        # frames
        self.right = RectangleRegion((self.screen_center[0]+300, self.screen_center[1]), self.half_width, self.half_height)
        self.left = RectangleRegion((self.screen_center[0]-300, self.screen_center[1]), self.half_width, self.half_height)
        self.right_wide = RectangleRegion((self.screen_center[0]+300, self.screen_center[1]), self.half_width+10, self.half_height+10)
        self.left_wide = RectangleRegion((self.screen_center[0]-300, self.screen_center[1]), self.half_width+10, self.half_height+10)

    def setupFirstSubjects(self):
        # Center of the screen.
        self.screen_center = (683,384)

        # frames
        self.right = RectangleRegion((self.screen_center[0]+300, self.screen_center[1]), self.half_width, self.half_height)
        self.left = RectangleRegion((self.screen_center[0]-300, self.screen_center[1]), self.half_width, self.half_height)
        self.right_wide = RectangleRegion((self.screen_center[0]+300, self.screen_center[1]), self.half_width+10, self.half_height+10)
        self.left_wide = RectangleRegion((self.screen_center[0]-300, self.screen_center[1]), self.half_width+10, self.half_height+10)

    # Returns a dictionary of experiment variables
    def parseVariables(self, line: List[str]):
        #print(line)
        if len(line) > 3 and line[3] == "stim1":
            try:
                if len(line) > 3 and line[3] == "stim1":
                    stim1 = line[5]
                    stim2 = line[10]
                    arrow = line[15]
                    emotion = line[20]
                return {
                    'stim1' : stim1,
                    'stim2' : stim2,
                    'arrow' : arrow,
                    'emotion' : emotion
                    }

            except:
                pass
        elif len(line) > 3 and line[3] == "target_side":
            try:
                if len(line) > 3 and line[3] == "target_side":
                    target_side = line[5]
                    position_emo = line[10]
                    position_neu = line[15]
                return {
                    'target_side' : target_side,
                    'position_emo' : position_emo,
                    'position_neu' : position_neu,
                    }

            except:
                pass
        return None

    def isResponse(self, line: Line) -> bool :
        return len(line) >= 2 and 'END' in line[0] and 'SAMPLES' in line[2]

    def isTraining(self, trial) -> bool:
        return 'Dis' in trial.features['stim1']

class Exp(Experiment):

    def __init__(self):
        super().__init__(None)
        self.n_trials = 80
        self.expected_features = {'stim1', 'stim2', 'arrow', 'emotion', 'target_side', 'position_emo', 'position_neu'}

    def selectEyetracker(self, input_file : str) -> None:
        logTrace ('Selecting Eyelink', Precision.NORMAL)
        self.eyetracker = Make_Eyelink()

    def processTrial(self, subject, trial, filename = None):
        if subject.id <= 3:
            self.eyetracker.setupFirstSubjects()

        logTrace ('Processing trial n°%i' % trial.getTrialId(), Precision.DETAIL)
        trial_number = trial.getTrialId()
        start_trial_time = trial.getStartTrial().getTime()

        if trial.isTraining():
            emo_position = self.eyetracker.left
            neu_position = self.eyetracker.right
        else:
            if 'left' in trial.features['target_side']:
                emo_position = self.eyetracker.left
                neu_position = self.eyetracker.right
            elif 'right' in trial.features['target_side']:
                emo_position = self.eyetracker.right
                neu_position = self.eyetracker.left
        regions = InterestRegionList([emo_position, neu_position])

        if trial.features['arrow'] ==  trial.features['target_side']:
            first_image_to_look = 'EMO'
            region_to_look = emo_position
            region_not_to_look = neu_position
        elif trial.features['arrow'] !=  trial.features['target_side']:
            first_image_to_look = 'NEU'
            region_to_look = neu_position
            region_not_to_look = emo_position

        if trial.saccades == []:
            logTrace ("Subject %i has no saccades at trial %i !" %(subject.id,trial_number), Precision.DETAIL)
            first_saccade = None
            first_saccade_pos = None
        else:
            first_saccade = trial.saccades[0].getStartTimeFromStartTrial()
            if region_to_look.point_inside(trial.saccades[0].getLastGazePosition()):
                first_saccade_pos = 'Correct'
            elif region_not_to_look.point_inside(trial.saccades[0].getLastGazePosition()):
                first_saccade_pos = 'Incorrect'
            else:
                first_saccade_pos = 'Miss'


        targetname = trial.features['stim1']

        response_entry = trial.getResponse()

        region_fixations = trial.getFixationTime(regions, emo_position)
        # First fixations
        try:
            first_fixation = next(fixation for fixation in region_fixations)
        except:
            first_fixation = None

        try:
            first_emo_fixation = next(fixation for fixation in region_fixations if fixation.on_target)
            capture_delay_emo_first = first_emo_fixation.getStartTimeFromStartTrial()
        except:
            first_emo_fixation = None
            capture_delay_emo_first = None

        try:
            first_neu_fixation = next(fixation for fixation in region_fixations if not fixation.on_target)
            capture_delay_neu_first = first_neu_fixation.getStartTimeFromStartTrial()
        except:
            first_neu_fixation = None
            capture_delay_neu_first = None

        # Time on target and distractors
        total_emo_fixation_time = sum(x.duration() for x in region_fixations if x.on_target)
        percent_emo_fixation_time = None
        total_neu_fixation_time = sum(x.duration() for x in region_fixations if not x.on_target)
        percent_neu_fixation_time = None
        total_target_fixation_time = sum(x.duration() for x in region_fixations if ((x.on_target and first_image_to_look == "EMO") or (not x.on_target and first_image_to_look == "NEU") ))
        percent_target_fixation_time = None
        if total_emo_fixation_time != 0 or total_neu_fixation_time != 0:
            percent_emo_fixation_time = total_emo_fixation_time/(total_neu_fixation_time+total_emo_fixation_time)*100
            percent_neu_fixation_time = total_neu_fixation_time/(total_neu_fixation_time+total_emo_fixation_time)*100
            percent_target_fixation_time = total_target_fixation_time/(total_neu_fixation_time+total_emo_fixation_time)*100
        # if total_emo_fixation_time == 0:
        #     total_emo_fixation_time = None
        #     percent_emo_fixation_time = None
        # if total_neu_fixation_time == 0:
        #     total_neu_fixation_time = None
        #     percent_neu_fixation_time = None

        # Determining blink category
        if trial.blinks == []:
            blink_category = "No blink"
        else:
            if first_fixation is not None:
                if trial.blinks[0].getStartTime() < first_fixation.getStartTime():
                    blink_category = "early capture"
                else:
                    blink_category = "late"
            else:
                blink_category = None


        try:
            first_target_fixation = next(fixation for fixation in region_fixations if ((fixation.on_target and first_image_to_look == 'EMO') or (not fixation.on_target and first_image_to_look == 'NEU')))
            capture_delay_target_first = first_target_fixation.getStartTimeFromStartTrial()
        except:
            first_target_fixation = None
            capture_delay_target_first = None

        # Error :
        if not trial.isStartValid(self.eyetracker.screen_center, self.eyetracker.valid_distance_center)[0]:
            error = "Not valid start"
            error_sac = "Not valid start"
        # elif (total_neu_fixation_time+total_emo_fixation_time) < 4000:
        #     error = "Low fixation"
        # Add sac amplitude ?
        elif blink_category == 'early capture':
            error = "Early blink"
            error_sac = "Early blink"
        elif first_fixation is None:
            error = "No fixation"
            error_sac = "No fixation"
        elif first_fixation.getStartTimeFromStartTrial() < 100:
             error = "Anticipation saccade"
             error_sac = "Anticipation saccade"
        # elif first_saccade <= 80:
        #      error_sac = "Anticipation saccade"
        # elif first_saccade > 700:
        #     error = "Saccade too long"
        else:
            if trial.isTraining():
                error = '0'
            else:
                if ((first_fixation.on_target and trial.features['arrow'] == trial.features['target_side'])
                    or (not first_fixation.on_target and trial.features['arrow'] != trial.features['target_side'])):
                    error = '0'
                else:
                    error = '1'
                if first_saccade_pos == 'Correct':
                    error_sac = '0'
                elif first_saccade_pos == 'Incorrect':
                    error_sac = '1'
                elif first_saccade_pos == 'Miss':
                    error_sac = 'Miss'

        # Writing data in result csv file
        s = [str(subject.id) + "-E", # Subject name
            subject.group,
            trial_number,
            trial.isTraining(),
            trial.eye,
            trial.features['emotion'],
            first_image_to_look,
            trial.features['stim1'],
            trial.features['stim2'],
            trial.features['target_side'],
            trial.features['arrow'],
            trial.features['position_emo'],
            trial.features['position_neu'],
            error,
            capture_delay_emo_first,
            capture_delay_neu_first,
            total_emo_fixation_time,
            total_neu_fixation_time,
            str(percent_emo_fixation_time).replace('.',','),
            str(percent_neu_fixation_time).replace('.',','),
            blink_category,
            first_saccade,
            capture_delay_target_first,
            error_sac,
            total_target_fixation_time,
            str(percent_target_fixation_time).replace('.',',')]

        if filename is None:
            f = open(getResultsFile(), 'a')
        else:
            f = open(filename, 'a')
        f.write(';'.join([str(x) for x in s]))
        f.write('\n')
        f.close()

    def computeCurveTrial(self, trial, region_fixation):
        res = [0 for i in range(0, trial.getStopTrial().getTime() - trial.getStartTrial().getTime())]
        for fixation in region_fixation:
            if fixation.on_target:
                for time in range(
                    fixation.getStartTimeFromStartTrial(),
                    fixation.getEndTimeFromStartTrial(),
                    2):
                    res[time] = 1
            else:
                for time in range(
                    fixation.getStartTimeFromStartTrial(),
                    fixation.getEndTimeFromStartTrial(),
                    2):
                    res[time] = -1
        return res

    def make_gnuplot_script(self, subject, emotion):
        f = open('plots/make_plot', 'w')
        f.write(
            '''
            set term 'png'
            set output 'plots/%s_%s.png'
            set yrange [-0.5:0.5]
            set datafile separator ";"
            plot '%s.csv'
            ''' % (subject.id, emotion, emotion) # smooth bezier w filledcurves above
        )
        f.close()

    def plotCurve(self, subject, curve, name):
        f = open('%s.csv' % name, 'w')
        for i in range(len(curve)):
            f.write('%i ; %s\n' % (i, str(curve[i])))
        f.close()
        self.make_gnuplot_script(subject, name)
        os.system('gnuplot plots/make_plot')

    def computeCurves(self, subject):
        def add_curves(x,y):
            res = [a + b for (a,b) in zip(x,y)]
            if len(x) < len(y):
                res += y[len(x):]
            elif len(y) < len(x):
                res += x[len(y):]
            return res

        def diff_curves(x,y):
            res = [a - b for (a,b) in zip(x,y)]
            if len(x) < len(y):
                res += [-1*b for b in y[len(x):]]
            elif len(y) < len(x):
                res += x[len(y):]
            return res

        def group_curve(x, e):
            i = 0
            res = []
            while i <= len(x):
                s = sum(y for y in x[i:i+e])
                res.append(s/e)
                i += e
            return res

        if subject.id <= 3:
            self.eyetracker.setupFirstSubjects()

        n = {
            'pos_target': 0,
            'pos': 0,
            'neg_target': 0,
            'neg': 0
        }
        curves = {
            'pos_target': [],
            'pos': [],
            'neg_target': [],
            'neg': []
        }

        for trial in subject.trials:
            if trial.isTraining():
                continue
            if 'left' in trial.features['target_side']:
                emo_position = self.eyetracker.left
                neu_position = self.eyetracker.right
            elif 'right' in trial.features['target_side']:
                emo_position = self.eyetracker.right
                neu_position = self.eyetracker.left
            target_emo = trial.features['arrow'] ==  trial.features['target_side']

            regions = InterestRegionList([emo_position, neu_position])

            region_fixations = trial.getFixationTime(regions, emo_position)

            res = self.computeCurveTrial(trial, region_fixations)
            s = trial.features['emotion']
            if target_emo:
                s += '_target'
            n[s] += 1
            curves[s] = add_curves(curves[s], res)

        for s in curves:
            for i in range(len(curves[s])):
                curves[s][i] /= n[s]
            curves[s] = group_curve(curves[s], 20)
            self.plotCurve(subject, curves[s], s)

        # diff_curve = diff_curves(curves['pos_target'], curves['neg_target'])
        # self.plotCurve(subject, diff_curve, 'diff')
        return curves

    # def leastSquares(curve1, curve2):
    #     """
    #     Computes the least square difference between the two curves.
    #     """
    #

#    def fit(curve, target):

    def evolutionScore(self, subject):
        # def masuperbecourbe(shift):
        #     a1 = shift[0] # scaling for the first part
        #     a2 = shift[1] # scaling for the second part
        #     b1 = shift[2]
        #     b2 = shift[3]
        #     m = shift[4] # middle
        #
        #     def f(i):
        #         if i < m:
        #             return a1 * ((i - m/2)/100)**2 + b1
        #         else:
        #             return a2 * ((i - 3*m/2)/100)**2 + b2
        #
        #     return numpy.vectorize(f)

        def parabols(shift, n_parabols, n_x):
            def f(i):
                i_parabol = 0
                while i_parabol < n_parabols - 1:
                    if i < shift[3*i_parabol+2]:
                        break
                    i_parabol += 1
                a = shift[3*i_parabol]
                b = shift[3*i_parabol+1]
                if i_parabol == 0:
                    m = shift[2]/2
                elif i_parabol == n_parabols - 1:
                    m = (n_x + shift[3*(i_parabol-1)+2])/2
                else:
                    m = (shift[3*i_parabol+2] + shift[3*(i_parabol-1)+2])/2
                return a * ((i - m)/100)**2 + b
            return numpy.vectorize(f)

        def get_coeff_of_curve(curve, name):

            n_parabols = 4

            t_train = numpy.array([x for x in range(len(curve))])

            def residu(shift, t, y):
                f_vec = parabols(shift, n_parabols, len(curve))
                return f_vec(t) - y

            shift_0 =[]
            for i in range(n_parabols):
                shift_0 += [1.0,0.0,int((i+1)*len(curve)/n_parabols)]
            shift_0 = numpy.array(shift_0)
            # [
            #     1.0, # parabol 1: a
            #     0.0, # parabol 1: b
            #     int(len(curve)/3), #sep 1
            #     -1.0, # parabol 2: a
            #     0.0, #parabol 2: b
            #    2*int(len(curve)/3), #sep 2
            #    1.0, # parabol 3: a
            #    0.0, #parabol 3: b
            # ])
            res = scipy.optimize.least_squares(residu, shift_0, args = (t_train, curve), loss='cauchy')
            print(res)

            # Plotting result
            self.plotCurve(subject, curve, name)
            f_vec = parabols(shift_0, n_parabols, len(curve))
            expected = f_vec(t_train)
            self.plotCurve(subject, expected, name + '_expected')
            f_vec = parabols(res.x, n_parabols, len(curve))
            result = f_vec(t_train)
            self.plotCurve(subject, result, name + '_result')

        curves = self.computeCurves(subject)
        for (name, curve) in curves.items():
            get_coeff_of_curve(curve, name)
        #
        # t_min = 0
        # t_max = 1
        # n_points = 100
        # rnd = numpy.random.RandomState(0)
        # t_train = numpy.linspace(t_min, t_max, n_points)
        # y_train = numpy.sin(0.2 * t_train) + 1.15 + rnd.randn(t_train.size)
        #
        # def residu(shift, t, y):
        #     return  numpy.sin(shift[0] * t) + shift[1] - y
        #
        # shift_0 = numpy.array([1.0, 0.0])
        #
        # res = scipy.optimize.least_squares(residu, shift_0, args = (t_train, y_train))
        # print(res)

        # diff_curve = self.computeCurve(subject)
        #
        # diff2 = group_curve(diff_curve, 2)
        # self.plotCurve(subject, diff2, 'diff2')
        #
        # diff20 = group_curve(diff_curve, 20)
        # self.plotCurve(subject, diff20, 'diff20')
        #
        # final_curve = diff20
        # xs = [i for i in range(len(final_curve))]
        # #interpol_curve = scipy.interpolate.interp1d(xs, diff20, kind='cubic', fill_value = 'extrapolate')
        # #interpol_curve = scipy.interpolate.BarycentricInterpolator(xs, diff20)
        #
        # # Smoothing
        # interpol_curve = scipy.interpolate.BSpline(xs, final_curve, 2)
        #
        # ys = [interpol_curve(x) for x in xs]
        # self.plotCurve(subject, ys, 'interpol')
        #
        # roots = [scipy.optimize.fsolve(interpol_curve, i)[0]
        #     for i in range(0,len(final_curve), int(len(final_curve)/10))
        # ]
        # print(roots)
        #
        # # removing duplicates:
        # roots2 = []
        # epsilon = 1
        # for root in roots:
        #     add = True
        #     for root2 in roots2:
        #         if abs(root - root2) < epsilon:
        #             add = False
        #             break
        #     if add:
        #         roots2.append(root)
        #
        # # adding beginning and ending
        # roots2 = [0] + roots2 + [xs[-1]]
        # roots2.sort()
        # print(roots2)
        #
        # # integration
        # integral_curve = []
        # for i in range(len(roots2)-1):
        #     a = roots2[i]
        #     b = roots2[i+1]
        #     ys = [final_curve[x] for x in xs if x >= a and x <= b]
        #     integral_curve.append((
        #         (a + b)/2,
        #         scipy.integrate.trapz(ys)
        #     ))
        #
        # # integral curve
        # xs = [x[0] for x in integral_curve]
        # ys = [x[1] for x in integral_curve]
        # print('coeff', numpy.corrcoef(xs, ys))



    def postProcess(self, filename: str):
        def initialize_variables(line):
            d = dict()
            d['subject_num'] = line[0]
            d['emotion'] = line[5]
            d['first_image_to_look'] = line[6]
            d['error'] = line[13]
            d['blink'] = line[20]
            try:
                d['first_sac'] = float(line[21])
            except:
                d['first_sac'] = line[21]
            try:
                d['first_target'] = float(line[22])
            except:
                d['first_target'] = line[22]
            try:
                d['total_target'] = float(line[24])
            except:
                d['total_target'] = line[24]
            return d

        with open(filename) as datafile:
            data = datafile.read()
        data_modified = open(filename, 'w')
        data = data.split('\n')
        data = [x.split(';') for x in data]
        subject = "Subject"
        sequence = []
        data_seq = []
        list_scores = ['first_sac', 'first_target', 'total_target']

        for line in data:
            if line[0] == "Subject":
                new_line = line
                new_line.append('First saccade sorting')
                new_line.append('First fixation target sorting')
                new_line.append('Total fixation target sorting')
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
                code = dic_variables['first_image_to_look'] + dic_variables['emotion']
                if code not in elements_list:
                    elements_list[code] = {}
                    mean_dic[code] = {}
                    for element in list_scores:
                        elements_list[code][element] = []
                        mean_dic[code][element] = None
                if dic_variables['first_sac'] != 'None' and "early" not in dic_variables['blink'] and ("0" in dic_variables['error'] or "1" in dic_variables['error']):
                    elements_list[code]['first_sac'].append(dic_variables['first_sac'])
                if dic_variables['first_target'] != 'None' and "early" not in dic_variables['blink'] and ("0" in dic_variables['error'] or "1" in dic_variables['error']):
                    elements_list[code]['first_target'].append(dic_variables['first_target'])
                if dic_variables['total_target'] != 'None' and "early" not in dic_variables['blink'] and ("0" in dic_variables['error'] or "1" in dic_variables['error']):
                    elements_list[code]['total_target'].append(dic_variables['total_target'])

            for code in mean_dic:
                for key in mean_dic[code]:
                    if len(elements_list[code][key]) != 0:
                        mean_dic[code][key] = sum(elements_list[code][key])/len(elements_list[code][key])

            for line in subject:
                dic_variables = initialize_variables(line)
                code = dic_variables['first_image_to_look'] + dic_variables['emotion']
                if code not in square_dic:
                    square_dic[code] = {}
                    SD_dic[code] = {}
                    for element in list_scores:
                        square_dic[code][element] = []
                        SD_dic[code][element] = None
                if dic_variables['first_sac'] != "None" and "early" not in dic_variables['blink'] and ("0" in dic_variables['error'] or "1" in dic_variables['error']):
                    square_dic[code]['first_sac'].append(squareSum(dic_variables['first_sac'], mean_dic[code]['first_sac']))
                if dic_variables['first_target'] != "None" and "early" not in dic_variables['blink'] and ("0" in dic_variables['error'] or "1" in dic_variables['error']):
                    square_dic[code]['first_target'].append(squareSum(dic_variables['first_target'], mean_dic[code]['first_target']))
                if dic_variables['total_target'] != "None" and "early" not in dic_variables['blink'] and ("0" in dic_variables['error'] or "1" in dic_variables['error']):
                    square_dic[code]['total_target'].append(squareSum(dic_variables['total_target'], mean_dic[code]['total_target']))

                for code in SD_dic:
                    for key in SD_dic[code]:
                        if len(square_dic[code][key]) != 0:
                            if len(square_dic[code][key]) > 1:
                                SD_dic[code][key] = sqrt(sum(square_dic[code][key])/(len(square_dic[code][key])-1))
                            else:
                                SD_dic[code][key] = sqrt(sum(square_dic[code][key])/len(square_dic[code][key]))

            for line in subject:
                dic_variables = initialize_variables(line)
                code = dic_variables['first_image_to_look'] + dic_variables['emotion']
                new_line = line
                for key in mean_dic[code]:
                    if key == 'first_sac':
                        score = dic_variables['first_sac']
                    elif key == 'first_target':
                        score = dic_variables['first_target']
                    elif key == 'total_target':
                        score = dic_variables['total_target']
                    if SD_dic[code][key] != None and score != "None" and "early" not in dic_variables['blink'] and ("0" in dic_variables['error'] or "1" in dic_variables['error']):
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
        return joinPaths(getResultsFolder(), 'visual_selection.csv')

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
            'First image to look',
            'Emotion target',
            'Neutral target',
            'TargetSide',
            'Arrow orientation',
            'Position emo',
            'Position neu',
            'Errors',
            'First time on emotional target',
            'First time on neutral target',
            'Total fixation time on emotional target',
            'Total fixation time on neutral target',
            '% fixation time on emotional target',
            '% fixation time on neutral target',
            'First blink type',
            'First saccade',
            'Capture delay target first',
            'Errors saccade',
            'Total fixation time on target',
            '% fixation time on target'
        ]))
        f.write('\n')
        f.close()


    # Creates an image scanpath for one trial.
    def scanpath(self, subject_id, trial, frequency : int):
        plt.clf()

        frame_color = (0,0,0)
        emo_color = (1,0,0)
        target_color = (0,1,0)
        x_axis = self.eyetracker.screen_center[0] * 2
        y_axis = self.eyetracker.screen_center[1] * 2
        plt.axis([0, x_axis, 0, y_axis])
        plt.gca().invert_yaxis()
        plt.axis('off')

        # Plotting frames
        if trial.isTraining():
            plotRegion(self.eyetracker.left, frame_color)
            plotRegion(self.eyetracker.right, frame_color)
        else:
            if 'left' in trial.features['target_side']:
                plotRegion(self.eyetracker.left, emo_color)
                plotRegion(self.eyetracker.right, frame_color)
            elif 'right' in trial.features['target_side']:
                plotRegion(self.eyetracker.left, frame_color)
                plotRegion(self.eyetracker.right, emo_color)

        if 'left' in trial.features['arrow']:
            plotRegion(self.eyetracker.left_wide, target_color)
        elif 'right' in trial.features['arrow']:
            plotRegion(self.eyetracker.right_wide, target_color)

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
        target_color = (0,1,0)
        emo_color = (1,0,0)

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
            ax = plt.axis([0,axis_x,0,axis_y])
            plt.gca().invert_yaxis()
            plt.axis('off')

            for j in range(max(0,elem-n_elem_drawn),elem+1):
                plotSegment(point_list_f[j], point_list_f[j+1], c = point_color)
            point_color = (1, point_color[1] - 1.0/nb_points , 0)

            if trial.isTraining():
                plotRegion(self.eyetracker.left, frame_color)
                plotRegion(self.eyetracker.right, frame_color)
            else:
                if 'left' in trial.features['target_side']:
                    plotRegion(self.eyetracker.left, emo_color)
                    plotRegion(self.eyetracker.right, frame_color)
                elif 'right' in trial.features['target_side']:
                    plotRegion(self.eyetracker.left, frame_color)
                    plotRegion(self.eyetracker.right, emo_color)

            if 'left' in trial.features['arrow']:
                plotRegion(self.eyetracker.left_wide, target_color)
            elif 'right' in trial.features['arrow']:
                plotRegion(self.eyetracker.right_wide, target_color)

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
            subject = Subject(self, data, n_subject, subject_cat, progress)

            self.evolutionScore(subject)
            return subject
