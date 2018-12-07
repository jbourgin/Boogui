#This script is dedicated to smi. It filters raw data, writing a new file containing saccades, fixations and blinks which are calculated. It is for now focused on an accurate calculation of fixation according to dispersion and velocity parameters. Compared to the algorithm comprise in the SMI software, it takes into account artifacts and allows to consider both dispersion and velocity.
import matplotlib.pyplot as plt
import re
from math import pow,sqrt,atan2,degrees
from string import *

from eyetracking.utils import *

#global parameters
min_dispersion = 40.0 #Around 1° of dispersion
size_screen = 56.6 # Monitor size in cm
distance_ppt = 74.0 # Distance between monitor and participant in cm
monitor_resolution = 1567.0 #  resolution of the monitor
min_fixation_duration = 16 #30 ms According to Eyetracking, a comprehensive guide to methods and measures (2011)
min_blink_duration = 16
#Minimal velocity, to detect saccades, and maximal velocity, to detect artifacts.
#60°/s. The eye must go through 1 px/ms to be above this threshold.
min_velocity = 0.06
#1000°/s. The eye must go through 37 px/ms to be above this threshold.
max_velocity = 1

#Reading files functions
def get_inter_filename():
    return "results_inter.txt"

def two_decimals(s):
    return "{:.2f}".format(float(s))

#Gets time according to type of line
def get_time_line(line):
    if line[0] == "SBLINK" or line[0] == "SSACC" or line[0] == "SFIX":
        return int(line[2])
    elif line[0] == "EBLINK" or line[0] == "ESACC" or line[0] == "EFIX":
        return int(line[3])
    elif line[0] == "MSG" or line[0] == "END":
        return int(line[1])
    else:
        return int(line[0])

def fixation_to_string(fixation):
    t0 = get_time_line(fixation['lines'][0])
    t1 = get_time_line(fixation['lines'][-1])
    return "Fixation from %ims to %ims, blink after : %r" % (t0, t1, fixation['blink_after'])

def fixations_to_string(fixations):
    return '\n'.join(['fixations : '] + [fixation_to_string(fixation) for fixation in fixations])

#Function to convert pixels to degrees
def convert_px_to_degrees(size_in_px):
    # Calculate the number of degrees that correspond to a single pixel. This will
    # generally be a very small value, something like 0.03.
    deg_per_px = degrees(atan2(.5*size_screen, distance_ppt)) / (.5*monitor_resolution)
    #print ('%s degrees correspond to a single pixel' % deg_per_px)
    # Calculate the size of the stimulus in degrees
    size_in_deg = size_in_px * deg_per_px
    #print ('The size of the stimulus is %s pixels and %s visual degrees' % (size_in_px, size_in_deg))
    return size_in_deg

#Returns X and Y coordinates of gaze position on a line
def get_point(line):
    return [float(line[3]),float(line[4])]

def barycentre_from_points(list_fix):
    x = 0
    y = 0
    max_x = -1500
    max_y = -1000
    min_x = 1500
    min_y = 1000
    previous_point = None
    counter = 0
    for elemt in list_fix:
        #Since we add false points at the beginning of the fixation to make saccades shorter, we don't add these make points in the barycenter calculation.
        if previous_point == None or (previous_point != None and (previous_point[0] != float(elemt[0]) or previous_point[1] != float(elemt[1]))):
            x += float(elemt[0])
            y += float(elemt[1])
            if float(elemt[0]) > max_x:
                max_x = float(elemt[0])
            if float(elemt[0]) < min_x:
                min_x = float(elemt[0])
            if float(elemt[1]) > max_y:
                max_y = float(elemt[1])
            if float(elemt[1]) < min_y:
                min_y = float(elemt[1])
            counter += 1
            previous_point = (float(elemt[0]),float(elemt[1]))

    if min_x - max_x > 50 or min_y - max_y > 50:
        return None
    else:
        return (x/counter,y/counter)

def compute_barycentre(lines):
    list_points = []
    for line in lines:
        x = get_point(line)[0]
        y = get_point(line)[1]
        list_points.append((x,y))

    return barycentre_from_points(list_points)

#Calculates velocity between two lines in degrees. The unit is calculated between the two lines involved. Division by 1000 stands for SMI (microseconds).
def compute_velocity_lines(line1,line2):
    t1 = get_time_line(line1)
    t2 = get_time_line(line2)
    unite = abs(t2 - t1)
    velocity_px = distance(get_point(line1),get_point(line2))/unite
    velocity_dg_per_ms = convert_px_to_degrees(velocity_px)

    return velocity_dg_per_ms

#Determines if a point is contained in the current fixation (from dispersion and velocity calculations)
def point_in_fixation(fixation, current_line):
    lines = fixation['lines']
    barycentre = compute_barycentre(lines)
    velocity = compute_velocity_lines(lines[len(lines)-1],current_line)
    return distance(barycentre,get_point(current_line)) <= min_dispersion and velocity <= min_velocity

#Determines fixation duration (in order to see if it is long enough to be considered as a fixation). Division by 1000 stands for SMI (microseconds).
def get_fixation_duration(lines):
    if len(lines) == 0:
        return False
    return int(lines[len(lines)-1][0]) - int(lines[0][0])

#Determines validity of fixation (from its duration)
def is_fixation_valid(fixations):
    lines = fixations['lines']
    return get_fixation_duration(lines) >= min_fixation_duration

#Writes line in an exportable format (string)
def export_line(line, result_file):
    result_file.write("\t".join(line) + "\n")

#Writes fixation in an exportable format (string). Assumes that dominant eye is always right. SFIX < lines < EFIX
def export_fixation(fixation, result_file):
    t1 = int(fixation[0][0])
    t2 = int(fixation[len(fixation)-1][0])
    begin_fix = "\t".join(["SFIX","R",str(t1)]) + "\n"
    result_file.write(begin_fix)
    for line in fixation:
        export_line(line, result_file)
    end_fix = "\t".join(["EFIX","R",str(t1),str(t2)]) + "\n"
    result_file.write(end_fix)

def get_max_duration(unite,p1,p2):
    max_duration = abs(round(2.2*convert_px_to_degrees(distance(p1,p2)))) +21 #in ms, Carpenter, 1988
    while max_duration % unite != 0:
        max_duration += 1

    return max_duration

def can_add_saccade(unite, fixation1, fixation2):
    t1 = int(fixation1[len(fixation1)-1][0])
    t2 = int(fixation2[0][0])
    p1 = get_point(fixation1[len(fixation1)-1])
    p2 = get_point(fixation2[0])
    max_duration = get_max_duration(unite,p1,p2)
    if t2 - t1 > max_duration:
        n_step = abs(round(max_duration/unite))
    else:
        n_step = abs(round((int(t2-t1))/unite))

    return n_step > 1

def make_saccade_between(unite, n_trial, fixation1, fixation2):
    t1 = int(fixation1[-1][0])
    t2 = int(fixation2[0][0])
    p1 = get_point(fixation1[-1])
    p2 = get_point(fixation2[0])

    max_duration = get_max_duration(unite,p1,p2)
    if t2 - t1 > max_duration:
        n_step = abs(round(max_duration/unite))
    else:
        n_step = abs(round((int(t2-t1))/unite))

    time = t1
    if n_step <= 1:
        return []

    lines = []
    for i in range(n_step-1):
        time += unite
        #Calculates next point coordinates and writes it in the subject file
        x = p1[0] + (p2[0] - p1[0])*(i+1)/n_step
        y = p1[1] + (p2[1] - p1[1])*(i+1)/n_step
        lines.append([str(time), 'SMP', str(n_trial+1), two_decimals(x), two_decimals(y)])

    return lines

#Writes saccades between fixations. Saccades are "manufactured". SSACC < lines < ESACC. Works only for SMI : x 1000.
def add_saccade_between(unite, n_trial, fixation1, fixation2, result_file):
    logTrace('Adding saccade between %s\nand\%s' % (str(fixation1),str(fixation2)), Precision.DETAIL)
    t1 = int(fixation1[-1][0])
    t2 = int(fixation2[0][0])
    p1 = get_point(fixation1[-1])
    p2 = get_point(fixation2[0])

    max_duration = get_max_duration(unite,p1,p2)

    logTrace('Max duration : %i' % max_duration, Precision.DETAIL)
    lines = make_saccade_between(unite, n_trial, fixation1, fixation2)
    begin_sac = "\t".join(["SSACC","R",str(t1+unite)]) + "\n"
    result_file.write(begin_sac)
    for line in lines:
        s = "\t".join(line[:3] + [two_decimals(line[3]), two_decimals(line[4])]) + "\n"
        result_file.write(s)
    if t2 - t1 > max_duration:
        end_sac = "\t".join(["ESACC","R",lines[0][0],str(t1+max_duration-unite)]) + "\n"
    else:
        end_sac = "\t".join(["ESACC","R",lines[0][0], lines[len(lines)-1][0]]) + "\n"
    result_file.write(end_sac)

    if t2 - t1 > max_duration:
        lines_to_add = []
        for t in range(int(lines[len(lines)-1][0]) + unite, t2, unite):
            lines_to_add.append([str(t), 'SMP', str(n_trial+1), str(p2[0]), str(p2[1])])
        return lines_to_add + fixation2

    else:
        return fixation2

def export_fixations(unite, n_trial, fixations, result_file):
    if len(fixations) > 0:
        if len(fixations) == 1:
            export_fixation(fixations[0]['lines'], result_file)
        else:
            if not(fixations[0]['blink_after']):
                if can_add_saccade(unite, fixations[0]['lines'], fixations[1]['lines']):
                    # TODO: ce test devrait prendre en compte la dispersion entre les deux fixations entières, pas seulement le premier point de la seconde fixation
                    if point_in_fixation(fixations[0], fixations[1]['lines'][0]):
                        # we merge the two fixations, and put the saccade in between
                        saccade_lines = make_saccade_between(unite, n_trial,fixations[0]['lines'], fixations[1]['lines'])
                        fixations[0]['lines'] = fixations[0]['lines'] + saccade_lines + fixations[1]['lines']
                        fixations[0]['blink_after'] = fixations[1]['blink_after']
                        fixations.pop(1)
                        export_fixations(unite, n_trial, fixations, result_file)
                    else:
                        export_fixation(fixations[0]['lines'], result_file)
                        fixations[1]['lines'] = add_saccade_between(unite, n_trial, fixations[0]['lines'], fixations[1]['lines'], result_file)
                        export_fixations(unite, n_trial, fixations[1:], result_file)
                else:
                    fixations[0]['lines'] = fixations[0]['lines'] + fixations[1]['lines']
                    fixations[0]['blink_after'] = fixations[1]['blink_after']
                    fixations.pop(1)
                    export_fixations(unite, n_trial, fixations, result_file)
            else:
                export_fixation(fixations[0]['lines'], result_file)
                export_fixations(unite, n_trial, fixations[1:], result_file)

def is_line_potential_blink(line):
    return (str(line[3]) == "0.00" and float(line[4]) < 10.00) or (str(line[4]) == "0.00" and float(line[3]) < 10.00)

#Count the number of consecutive zero lines in a potential blink
def count_zeros(trial,blink_beginning,blink_ending,blink_threshold):
    count_zero = 0
    for n_line in range(blink_beginning,blink_ending+1):
        if is_line_potential_blink(trial[n_line]):
            count_zero += 1
            if count_zero >= blink_threshold:
                return True
        else:
            count_zero = 0

    return False

def is_line_recording(line):
    try:
        float(line[3])
        float(line[4])
        return line[1] == "SMP"
    except:
        return False

#Gets blinks
def get_blink(trial,unite):
    blink_beginning = None
    blink_ending = None
    blink_list = []

    trial_filtered = [line for line in trial if is_line_recording(line)]

    stabilization_length = 8

    for n_line in range(0,len(trial_filtered)):
        line = trial_filtered[n_line]
        #We are in a blink if both x and y positions equal zero or are under ten
        if is_line_potential_blink(line):

            #If both positions are under zero, it may be due to a calibration issue rather than to a blink. This remains to be verified but should be very rare.
            if "-" in str(line[3]) and "-" in str(line[4]):
                print(line," is this negativity odd ?")

            if blink_beginning == None :
                velocity_stabilized_before = 0
                velocity_stabilized_after = 0
                blink_beginning = 0
                blink_ending = len(trial_filtered)-1

                #Calculates the beginning of the blink from velocity (needs a stabilization of 8 lines)
                for reverse_line in reversed(range(0,n_line)):
                    velocity = compute_velocity_lines(trial_filtered[reverse_line-1],trial_filtered[reverse_line])
                    if velocity >= min_velocity :
                        velocity_stabilized_before = 0
                    else:
                        velocity_stabilized_before +=1
                        if velocity_stabilized_before == stabilization_length:
                            blink_beginning = reverse_line+stabilization_length
                            break

        #We leave the blink if at least one position gets back above zero (one can remain negative). We take 10 to leave a small margin.
        elif blink_beginning != None and not is_line_potential_blink(line):
            #When the blink stops, calculates the ending of the blink from velocity (needs a stabilization of 8 lines)
            velocity = compute_velocity_lines(trial_filtered[n_line-1],trial_filtered[n_line])
            if velocity >= min_velocity :
                velocity_stabilized_after = 0
            else:
                velocity_stabilized_after +=1
                if velocity_stabilized_after == stabilization_length:
                    blink_ending = n_line-stabilization_length

        #Minimal duration of 20 ms for zeros (signal loss).
                    if count_zeros(trial,blink_beginning,blink_ending,min_blink_duration/unite):
                        blink_list.append((trial_filtered[blink_beginning][0],trial_filtered[blink_ending][0]))
                    blink_beginning = None
                    blink_ending = None

    # test if blink stops at the end of the trial
    if blink_beginning != None and count_zeros(trial,blink_beginning,blink_ending,min_blink_duration/unite):
        blink_list.append((trial_filtered[blink_beginning][0],trial_filtered[blink_ending][0]))
    return blink_list

#Elements of fixation dictionary are reinitialized
def empty_fixation():
    return {'blink_after' : False, 'lines' : []}

def linear_interpolation(unite,n_trial,line1,line2):

    point_list = []

    t1 = int(line1[0])
    t2 = int(line2[0])
    p1 = get_point(line1)
    p2 = get_point(line2)
    n_step = abs(round((int(t2-t1))/unite))
    if n_step <= 1:
        return None
    for i in range(n_step-1):
        #Calculates next point coordinates and appends it to the list to return
        x = p1[0] + (p2[0] - p1[0])*(i+1)/n_step
        y = p1[1] + (p2[1] - p1[1])*(i+1)/n_step
        new_line = [str(t1+(unite*(i+1))), 'SMP', str(n_trial), "{:.2f}".format(x), "{:.2f}".format(y)]
        point_list.append(new_line)

    return point_list

def get_file_by_name(subject_file):
    sample = -1
    datafile = open(subject_file,"r")

    #File conversion in list.
    data = datafile.read()
    data = list(data.splitlines())

    #We add a tabulation and space separator.
    data = [re.split("[\t ]+",line) for line in data]

    #We divide the list in a list of trials. A trial begins with a start_trial line, and ends with a stop_fixation line.
    seq = []
    data_seq = []
    for e in data:
        if len(e) > 5 and e[5] == "start_trial":
            data_seq.append(seq)
            seq = [e]
        else :
            seq.append(e)

    #We add the last sequence.
    data_seq.append(seq)

    #We remove what is between the end of a sequence and the beginning of another to avoid taking into account non relevant saccades.
    for j in range(len(data_seq)):
        seq = data_seq[j]
        i = 1
        for line in seq:
            if len(line) > 5 and line[5] == "stop_trial":
                break
            i += 1
        data_seq[j] = seq[:i]

    data = data_seq

    first_seq = data[0]
    data = data[1:]

    return data

def get_unit_pre_transfo(trial):
    for i in range(1,len(trial)):
        try:
            return int(trial[i+1][0]) - int(trial[i][0])
        except:
            continue

    return None

def processSubject(subject_file: str, result_file : str) -> None :
    createTmpFolder()
    data = get_file_by_name(subject_file)

    data_1000 = []
    data_filtered = []
    data_filtered2 = []
    artifact_percentage = []

    #We transform microseconds into milliseconds.
    for trial in data:
        trial_1000 = []
        last_time = None

        for line in trial:
            try:
                int(line[0])
                new_time = round(int(line[0])/1000)
                #We make sure that every recording line has a different time.
                if is_line_recording(line):
                    if last_time == None :
                        last_time = new_time
                    else:
                        if last_time == new_time :
                            new_time += 1
                        last_time = new_time

                new_line = [str(new_time)] + line[1:]
                trial_1000.append(new_line)

            except:
                trial_1000.append(line)

        data_1000.append(trial_1000)

    #Gets unite from calculation between two lines
    unite = get_unit_pre_transfo(data_1000[0])

    total_blinks = {}
    # Blink removal
    for n_trial in range(len(data_1000)):
        trial = data_1000[n_trial]

        blinks = get_blink(trial,unite)
        total_blinks[str(n_trial)] = [blink for blink in blinks]

        logTrace('Blinks were retrieved. Here is the list \n ' + str(blinks), Precision.NORMAL)
        print_message = True
        trial_filtered = []
        for line in trial:
            if is_line_recording(line):
                t = get_time_line(line)
                #If time is superior to beginning time of first element of blink list, we must print the beginning of the blink.
                if len(blinks) > 0 and t >= int(blinks[0][0]):
                    if print_message:
                        mess = ["SBLINK", "R", blinks[0][0]]
                        trial_filtered.append(mess)
                        print_message = False

                    #If time is superior to ending time of first element of blink list, we print the ending of the blink.
                    if t > int(blinks[0][1]):
                        mess = ["EBLINK", "R", blinks[0][0], blinks[0][1]]
                        trial_filtered.append(mess)
                        print_message = True
                        blinks.pop(0)
                else:
                    trial_filtered.append(line)
            else:
                if len(line) > 8 and line[6] == "sujet" and line[8] == "repondu" and not print_message and int(blinks[0][1]) < int(line[0]):
                    mess = ["EBLINK", "R", blinks[0][0], blinks[0][1]]
                    trial_filtered.append(mess)
                    print_message = True
                    blinks.pop(0)

                elif len(line) > 5 and line[5]== "stop_trial" and not print_message:
                    mess = ["EBLINK", "R", blinks[0][0], blinks[0][1]]
                    trial_filtered.append(mess)
                trial_filtered.append(line)

        data_filtered.append(trial_filtered)

    messages = []
    n_trial = 0
    #Removing artifacts
    for trial in data_filtered:
        #Artifacts indicator (will provide a percentage to see if the trial is worth keeping)
        artifact_count = 0
        nb_lines = 0
        n_trial += 1
        previous_not_artifacted_line = None
        post_added_line = 0
        trial_filtered = []
        point_list = []
        artifact_got = False

        for i_line in range (0,len(trial)):
            if is_line_recording(trial[i_line]):
                nb_lines += 1
                current_line = trial[i_line]

                if previous_not_artifacted_line == None:
                    previous_not_artifacted_line = current_line

                #We compute the velocity between the previous point and the current
                elif not artifact_got:
                    velocity = compute_velocity_lines(previous_not_artifacted_line,current_line)

                #If the velocity is above the threshold, we add the previous points to the list and look for the next point without artifact.
                    if velocity >= max_velocity:
                        artifact_got = True
                        artifact_count += 1
                        for elt in range (post_added_line,i_line):
                            if is_line_recording(trial[elt]):
                                trial_filtered.append(trial[elt])
                            post_added_line = i_line
                    else:
                        previous_not_artifacted_line = current_line

                elif artifact_got:
                    velocity = compute_velocity_lines(previous_not_artifacted_line,current_line)

                    #Once we have found a correct point, we do the linear interpolation and add the created points to the list. We then go back to the initial for loop.
                    if velocity < max_velocity :
                        point_list = linear_interpolation(unite,n_trial,previous_not_artifacted_line,current_line)
                        if point_list != None:
                            for elt in point_list:
                                trial_filtered.append(elt)
                            post_added_line = i_line
                            previous_not_artifacted_line = current_line
                            artifact_got = False
                            point_list = []
                    else:
                        artifact_count += 1

            else:
                messages.append(trial[i_line])

        #We add the end of the trial
        for line in trial[post_added_line:]:
            if not artifact_got and is_line_recording(line):
                trial_filtered.append(line)

        data_filtered2.append(trial_filtered)

        #If our trial has no valid lines (blink trials).
        if nb_lines > 0:
            artifact_percentage.append((artifact_count/nb_lines)*100)
        else:
            artifact_percentage.append(0)

    results = open(joinPaths(getTmpFolder(), get_inter_filename()), "w")
    for n_trial in range(len(data_filtered2)):
        trial = data_filtered2[n_trial]
        print('Trial number %i' % n_trial)

        fixations = []
        current_fixation = empty_fixation()

        for line in trial:
            t = get_time_line(line)

            #We note blinks after corresponding fixations.
            if len(total_blinks[str(n_trial)]) > 0 and t > int(total_blinks[str(n_trial)][0][1]):
                logTrace('Blink encountered: ' + str(line), Precision.DETAIL)
                current_fixation['blink_after'] = True
                total_blinks[str(n_trial)].pop(0)
                logTrace('Saving fixation', Precision.NORMAL)
                logTrace('fixation : ' + str(current_fixation), Precision.DETAIL)
                if is_fixation_valid(current_fixation):
                    fixations.append(current_fixation)
                current_fixation = empty_fixation()
                current_fixation['lines'] = [line]

            #We determine for each line if it is contained within the same fixation.
            #We do not consider negative or close to zero lines, for they are often noise.
            else:
                if float(line[3]) < 10.00 and float(line[4]) < 10.00:
                    continue
                elif current_fixation['lines'] == []:
                    current_fixation['lines'] = [line]
                elif (point_in_fixation(current_fixation, line)):
                    current_fixation['lines'].append(line)
                else:
                    logTrace('Point %s not in fixation' % str(get_point(line)), Precision.NORMAL)
                    logTrace('Saving fixation', Precision.NORMAL)
                    logTrace('fixation : ' + str(current_fixation), Precision.DETAIL)
                    if is_fixation_valid(current_fixation):
                        fixations.append(current_fixation)
                    elif len(fixations) > 0 and not fixations[-1]['blink_after']:
                        # We try to put back points in the previous fixation
                        for line2 in current_fixation['lines']:
                            if point_in_fixation(fixations[-1], line2):
                                fixations[-1]['lines'].append(line2)
                    current_fixation = empty_fixation()
                    current_fixation['lines'] = [line]

        #For the last fixation
        if is_fixation_valid(current_fixation):
            fixations.append(current_fixation)

        # Writing fixations in file
        logTrace("Exporting fixations", Precision.NORMAL)
        logTrace(fixations_to_string(fixations), Precision.DETAIL)
        export_fixations(unite, n_trial, fixations, results)
    results.close()

    #Writing messages at the right place
    results_inter = open(joinPaths(getTmpFolder(), get_inter_filename()),"r")
    results = open(joinPaths(getTmpFolder(), result_file),"w")

    #Converting file in list
    data = results_inter.read()
    data = list(data.splitlines())
    data = [re.split("[\t ]+",line) for line in data]
    results_inter.close()

    min_message = 0

    def print_message(message : str) -> None :
        if len(message) > 5 and message[5] == "start_trial":
        #We write the unit on the first line of the trial.
            mess = message + [" Unite "] + [str(unite)] + [" Artifact_percentage "] + [str(artifact_percentage[0])] + [" %"]
            artifact_percentage.pop(0)
            results.write("\t".join(mess) + "\n")
        elif len(message) > 5 and message[5] == "stop_trial":
            mess1 = [str(int(message[0]) - 1)] + message[1:5] + ["features:"] + message[6:]
            mess2 = message[:6]
            results.write("\t".join(mess1) + "\n")
            results.write("\t".join(mess2) + "\n")
        else:
            results.write("\t".join(message) + "\n")

    for line in data:
        t = get_time_line(line)
        for n in range(min_message,len(messages)):
            message = messages[n]
            if len(message) > 0 and (message[0] == "SBLINK" and t >= int(message[2])) or (message[0] == "EBLINK" and t >= int(message[3])) or (message[1] == "MSG" and t >= int(message[0])):
                min_message += 1
                print_message(message)
        results.write("\t".join(line) + "\n")


    # Printing last messages
    for n in range(min_message,len(messages)):
        message = messages[n]
        print_message(message)

    results.close()
