from eyetracking.eyelink import *
from eyetracking.interest_region import *

class Recherche_visuelle(Experiment):

    #Center of the screen.
    screen_center = (512,384)

    valid_distance_center = 125 #3 degres of visual angle 95 (+ marge)

    # Initializing regions of interest
    half_width = 163
    half_height = 115

    frame_list_1 = InterestRegionList([
        InterestRegion((164, 384), half_width, half_height),
        InterestRegion((860, 384), half_width, half_height)
    ])

    frame_list_3 = InterestRegionList([
        InterestRegion((266, 630), half_width, half_height),
        InterestRegion((758, 630), half_width, half_height),
        InterestRegion((266, 138), half_width, half_height),
        InterestRegion((758, 138), half_width, half_height)
    ])

    frame_list_5 = InterestRegionList([
        InterestRegion((164, 384), half_width, half_height),
        InterestRegion((860, 384), half_width, half_height),
        InterestRegion((266, 630), half_width, half_height),
        InterestRegion((758, 630), half_width, half_height),
        InterestRegion((266, 138), half_width, half_height),
        InterestRegion((758, 138), half_width, half_height)
    ])

    # Patients with inhibition difficulties
    list_patients_cong = [13,14]

    # Returns a dictionary of experiment variables
    @staticmethod
    def parseVariables(line: List[str]):
        if len(line) > 24 and line[8] == "tgt_hor":
            try:
                if len(line) > 24 and line[8] == "tgt_hor":
                    target_hp = int(line[10]) + Recherche_visuelle.screen_center[0]
                    target_vp = int(line[15]) + Recherche_visuelle.screen_center[1]
                    num_of_dis = int(line[5])
                    cor_resp = int(line[20])
                    response = int(line[24])
                    if target_hp < Recherche_visuelle.screen_center[0]:
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

    @staticmethod
    def isResponse(line: List[str]) -> bool :
        return len(line) >= 6 and 'repondu' in line[5]

    @staticmethod
    def isTraining(trial) -> bool:
        return 'face' in trial.getStimulus()

    @staticmethod
    def processTrial(subject, trial):
        print('Processing trial n°%i' % trial.getTrialId())
        trial_number = trial.getTrialId()

        if trial.saccades == []:
            print(subject.subject_number,trial_number,"Subject has no saccades!")

        if trial.features['num_of_dis'] == 1:
            frame_list = Recherche_visuelle.frame_list_1
        elif trial.features['num_of_dis'] == 3:
            frame_list = Recherche_visuelle.frame_list_3
        elif trial.features['num_of_dis'] == 5:
            frame_list = Recherche_visuelle.frame_list_5

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
        if ((trial.features['target_hp'] < Recherche_visuelle.screen_center[0] and trial.features['cor_resp'] == 1)
        or (trial.features['target_hp'] > Recherche_visuelle.screen_center[0] and trial.features['cor_resp'] == 2)):
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
        if (not trial.isStartValid(Recherche_visuelle.screen_center, Recherche_visuelle.valid_distance_center)
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

    #Creates an image scanpath for one trial.
    @staticmethod
    def scanpath(trial):#,nb_distractors,targetname,target_hp,target_vp,response_time,frame_list,distance_x,distance_y):
        print('scanpath')
        print(trial.features)
        '''
        point_list = []
        nb_points = 0
        color = (1,1,0)

        for line in trial:
            if Eyelink.is_line_recording(line):
                point_list.append([float(line[1]),float(line[2])])
            elif len(line) >= 5 and line[3] == "sujet" and line[4] == "a":
                break
        nb_points = float(len(point_list))

        plt.axis([0,1024,0,768])
        plt.gca().invert_yaxis()
        plt.axis('off')

        #Draws distractors and target frames.
        for i in range(0,len(point_list)-1):
            plot_segment([point_list[i][0],point_list[i+1][0]],[point_list[i][1],point_list[i+1][1]],c=color)
            color = (1, color[1] - 1.0/nb_points , 0)

        if nb_distractors == "1":
            if (target_hp,target_vp) == frame_list[0]:
                plot_target(frame_list[0],cor_resp,(0,0,0),distance_x,distance_y)
                plot_frame(frame_list[5],(0,0,0),distance_x,distance_y)
            else:
                plot_target(frame_list[5],cor_resp,(0,0,0),distance_x,distance_y)
                plot_frame(frame_list[0],(0,0,0),distance_x,distance_y)

        elif nb_distractors == "3":
            for i in range (1,5):
                if (target_hp,target_vp) == frame_list[i]:
                    plot_target(frame_list[i],cor_resp,(0,0,0),distance_x,distance_y)
                else:
                    plot_frame(frame_list[i],(0,0,0),distance_x,distance_y)
        elif nb_distractors == "5":
            for i in range (0,6):
                if (target_hp,target_vp) == frame_list[i]:
                    plot_target(frame_list[i],cor_resp,(0,0,0),distance_x,distance_y)
                else:
                    plot_frame(frame_list[i],(0,0,0),distance_x,distance_y)

        targetname = targetname.replace("jessi\\Images_finales\\","")
        targetname = targetname.replace(".png","")
        response_time = int(response_time)

        plt.text(float(target_hp)-(10*len(targetname)),float(target_vp),targetname)
        plt.text(800,-20,"response_time = " + str(response_time))
        '''
