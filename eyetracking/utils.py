from typing import Tuple
from math import pow, sqrt
import os, shutil
from enum import Enum
import collections

#############################
############ Log ############
#############################

class Precision(Enum):
    TITLE = 0
    INPUT = 1
    OUTPUT = 1
    NORMAL = 3
    DETAIL = 5
    ERROR = 0

precision_level = 0

def print_trace(message, precision):
    tabs = '\t'.join(['' for i in range(precision.value)])
    print(tabs + message.replace('\n','\n' + tabs))

def logTrace(message, precision):
    if precision.value <= precision_level:
        print_trace(message, precision)


#############################
# Interest regions and plot #
#############################

# Type for points describing gaze positions on the screen.
Point = Tuple[int,int]

def distance(point1 : Point, point2 : Point) -> float:
    return sqrt(pow(point2[0]-point1[0],2) + pow(point2[1] - point1[1],2))

def joinPaths(path1: str, path2: str) -> str:
    return os.path.join(path1, path2)

#############################
###### Data management ######
#############################

# ref_dict is a dict which every key refers to a list. If key of new_dict already exists in ref_dict, we update the already existing list. Else we create a new list with first element being value from new_dict.
def updateListDict(ref_dict, new_dict):
    for key, value in new_dict.items():
        if key in ref_dict:
            ref_dict[key].append(value)
        else:
            ref_dict[key] = [value]

def loadExperiments():
    """
    Dynamically loads all experiments from the experiments folder
    Returns a dictionary associating filenames to Experiment objects
    """
    path = 'experiments'
    files = [f for f in os.listdir(path)
        if (os.path.isfile(os.path.join(path, f)) and
            '.py' in f and
            '__init__' not in f
        )]

    experiments = dict()
    for file in files:
        filename = file.split('.')[0] # Filename without .py extension
        module_name = 'experiments.' + filename
        logTrace('Loading experiment' + module_name, Precision.NORMAL)
        mod = __import__(module_name, fromlist=['Exp'])
        klass = getattr(mod, 'Exp')
        experiments[filename] = klass()
    return experiments

#############################
######## Postprocess ########
#############################

# No longer used, replaced with numpy.nanstd
def squareSum(score: float, global_mean: float):
    return (float(score) - global_mean)*(float(score) - global_mean)

# Return true if val is outlier (far from mean by nbSD standard deviations, 3 by default)
# val may be float or string convertible to float
def isOutlier(val, mean, sd, nbSD=3) -> bool:
    return float(val) < (mean-(nbSD*sd)) or float(val) > (mean+(nbSD*sd))

#############################
############ IO #############
#############################

def getTmpFolder() -> str:
    return '_tmp'

def clearTmpFolder() -> None:
    folder = getTmpFolder()
    shutil.rmtree('%s' % (getTmpFolder()), ignore_errors=True)

def createTmpFolder() -> None:
    if not os.path.exists(getTmpFolder()):
        os.makedirs(getTmpFolder())

def getResultsFolder() -> str:
    return '_results'

def createResultsFolder() -> None:
    if not os.path.exists(getResultsFolder()):
        os.makedirs(getResultsFolder())

def getScanpathsFolder() -> str:
    return '_scanpaths'

def createScanpathsFolder() -> None:
    if not os.path.exists(getScanpathsFolder()):
        os.makedirs(getScanpathsFolder())

#############################
####### Miscellaneous #######
#############################

def isFloat(s):
    try:
        float(s)
        return True
    except ValueError:
        logTrace("Can't make float of {0}".format(s), Precision.OUTPUT)
        return False

def skip():
    1

def nested_dict():
    return collections.defaultdict(nested_dict)
