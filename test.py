from eyetracking.Recherche_visuelle import *
from eyetracking.smi_correction import processSubject
from eyetracking.utils import *

eyetracker = Make_Smi()

experiment = Recherche_visuelle(eyetracker)

#subject_file = 'data/sub_28.txt'
subject_file = 'data/subject-23Samples.txt'
result_file = 'result23.txt'
processSubject(subject_file, result_file)

datafile = open(joinPaths(getTmpFolder(), result_file),"r")

#File conversion in list.
data = datafile.read()
data = list(data.splitlines())

import re #To format data lists

#We add a tabulation and space separator.
data = [re.split("[\t ]+",line) for line in data]

#s = Subject(experiment, data, 28, "SAS")
s = Subject(experiment, data, 23, "SJS")

for trial in s.trials:
    experiment.processTrial(s, trial)

experiment.scanpath_video(5, s.trials[0])
