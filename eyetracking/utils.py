from typing import Tuple
from math import pow, sqrt

# Type for points describing gaze positions on the screen.
Point = Tuple[int,int]

def distance(point1 : Point, point2 : Point) -> float:
    return sqrt(pow(point2[0]-point1[0],2) + pow(point2[1] - point1[1],2))
