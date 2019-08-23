from typing import Tuple
from math import pow, sqrt
import os, shutil

# Type for points describing gaze positions on the screen.
Point = Tuple[int,int]

def distance(point1 : Point, point2 : Point) -> float:
    return sqrt(pow(point2[0]-point1[0],2) + pow(point2[1] - point1[1],2))

def joinPaths(path1: str, path2: str) -> str:
    return os.path.join(path1, path2)

def squareSum(score: float, global_mean: float):
    return (float(score) - global_mean)*(float(score) - global_mean)

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

from enum import Enum
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

def skip():
    1
