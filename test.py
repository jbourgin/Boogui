from eyetracking.Recherche_visuelle import *

myEyelink = Make_Eyelink()

experiment = Recherche_visuelle(myEyelink)

subject_file = 'data/sub_28.txt'

datafile = open(subject_file,"r")

#File conversion in list.
data = datafile.read()
data = list(data.splitlines())

import re #To format data lists

#We add a tabulation and space separator.
data = [re.split("[\t ]+",line) for line in data]

s = Subject(experiment, data, 28, "SAS")

for trial in s.trials:
    experiment.processTrial(s, trial)

experiment.scanpath_video(5, s.trials[0])
