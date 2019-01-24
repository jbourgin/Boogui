from eyetracking.Visual_search import *
from eyetracking.smi_correction import processSubject
from eyetracking.utils import *

#eyetracker = Make_Eyelink()
#subject_file = 'data/sub_28.txt'

eyetracker = Make_Smi()
subject_file = 'data/subject-23Samples.txt'

experiment = Visual_search(eyetracker)

subject = experiment.processSubject(subject_file)

for trial in subject.trials:
    experiment.processTrial(subject, trial)

experiment.scanpathVideo(5, subject.trials[0])
