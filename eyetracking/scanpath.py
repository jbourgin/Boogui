import matplotlib.pyplot as plt
from eyetracking.interest_region import *

def plot_segment(point1 : Point, point2 : Point, c = 'black', alpha = 1.0) -> None:
	if point1[0] == point2[0] and point1[1] == point2[1]:
		plt.plot([point1[0],point2[0]+1],[point1[1],point2[1]+1],c=c, alpha = alpha)
	else:
		plt.plot([point1[0],point2[0]],[point1[1],point2[1]],c=c, alpha = alpha)

def plot_rectangle(center : Point, color, half_width, half_height) -> None:
	lu_corner = [center[0]-half_width,center[1]+half_height]
	lb_corner = [center[0]-half_width,center[1]-half_height]
	ru_corner = [center[0]+half_width,center[1]+half_height]
	rb_corner = [center[0]+half_width,center[1]-half_height]
	plot_segment(lu_corner, lb_corner, c=color)
	plot_segment(lb_corner, rb_corner, c=color)
	plot_segment(rb_corner, ru_corner, c=color)
	plot_segment(ru_corner, lu_corner, c=color)

def plot_region(region : InterestRegion, color) -> None:
    plot_rectangle(region.center, color, region.half_width, region.half_height)
