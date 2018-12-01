from eyetracking.Recherche_visuelle import *

experiment = Recherche_visuelle()

myEyelink = Eyelink(experiment)

subject_file = 'data/sub_28.txt'

datafile = open(subject_file,"r")

#File conversion in list.
data = datafile.read()
data = list(data.splitlines())

import re #To format data lists

#We add a tabulation and space separator.
data = [re.split("[\t ]+",line) for line in data]

s = Subject(myEyelink, data)

print(s)

experiment.processTrial(s, 0)
