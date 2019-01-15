from math import sqrt
from typing import TypeVar, Union, List
from eyetracking.utils import *

#Type fof interest regions
InterestRegion = TypeVar('Region')
InterestRegionList = TypeVar('RegionList')
#define a rectangular region of interest
class InterestRegion:

    def __init__(self, p : Point, hw : int, hh : int, type : str):
        if type != 'RECTANGLE' and type != 'ELLIPSE':
            print('Expected type RECTANGLE or ELLIPSE, got %s', type)
        else:
            self.type = type
            self.center = p
            self.half_width = hw
            self.half_height = hh

    def __str__(self) -> str :
        return 'Rectangular region centered at (%i,%i), half-width = %i and half_height = %i' % (self.center[0], self.center[1], self.half_width, self.half_height)

    def point_inside(self, p: Point) -> bool :
        (x,y) = p
        if self.type == 'RECTANGLE':
            return (x >= self.center[0] - self.half_width
                and x <= self.center[0] + self.half_width
                and y >= self.center[1] - self.half_height
                and y <= self.center[1] + self.half_height)
        elif self.type == 'ELLIPSE':
            return false
            # TODO !

    def isTarget(self, target_center : Point) -> bool :
        return target_center == self.center

class InterestRegionList:

    def __init__(self, regions : List[InterestRegion]):
        self.regions = [x for x in regions]

    def getRegions(self) -> List[InterestRegion]:
        return self.regions

    # Returns the closest region to the given point
    def find_minimal_distance(self, point : Point) -> InterestRegion:
        minimal_distance = distance(self.regions[0].center, point)
        minimal_region = self.regions[0]
        for region in self.regions[1:]:
        	ampl = distance(region.center, point)
        	if ampl < minimal_distance:
        		minimal_distance = ampl
        		minimal_region = region

        return minimal_region

    def point_inside(self, point : Point) -> Union[None,InterestRegion]:
        try:
            return(next(region for region in self.regions if region.point_inside(point)))
        except StopIteration:
            return None
