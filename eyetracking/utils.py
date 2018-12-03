from typing import Tuple
from math import pow, sqrt
import os, shutil

# Type for points describing gaze positions on the screen.
Point = Tuple[int,int]

def distance(point1 : Point, point2 : Point) -> float:
    return sqrt(pow(point2[0]-point1[0],2) + pow(point2[1] - point1[1],2))

def joinPaths(path1: str, path2: str) -> str:
    return os.path.join(path1, path2)

def getTmpFolder() -> str:
    return '_tmp'

def clearTmpFodler() -> None:
    folder = getTmpFolder()
    shutil.rmtree('%s' % (getTmpFolder()), ignore_errors=True)
