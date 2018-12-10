import matplotlib.pyplot as plt
import os
from eyetracking.utils import *
from eyetracking.interest_region import *

def plotSegment(point1 : Point, point2 : Point, c = 'black', alpha = 1.0) -> None:
	if point1[0] == point2[0] and point1[1] == point2[1]:
		plt.plot([point1[0],point2[0]+1],[point1[1],point2[1]+1],c=c, alpha = alpha)
	else:
		plt.plot([point1[0],point2[0]],[point1[1],point2[1]],c=c, alpha = alpha)

def plotRectangle(center : Point, color, half_width, half_height) -> None:
	lu_corner = [center[0]-half_width,center[1]+half_height]
	lb_corner = [center[0]-half_width,center[1]-half_height]
	ru_corner = [center[0]+half_width,center[1]+half_height]
	rb_corner = [center[0]+half_width,center[1]-half_height]
	plotSegment(lu_corner, lb_corner, c=color)
	plotSegment(lb_corner, rb_corner, c=color)
	plotSegment(rb_corner, ru_corner, c=color)
	plotSegment(ru_corner, lu_corner, c=color)

def plotRegion(region : InterestRegion, color) -> None:
    plotRectangle(region.center, color, region.half_width, region.half_height)

def saveImage(folder : str, image_name: str) -> None:
    if not os.path.exists(folder):
        os.makedirs(folder)
    plt.savefig(joinPaths(folder, image_name))

def makeVideo(images : List[str], outvid, fps=20, size=None, format='XVID'):
    '''
    Create a video from a list of images.
 
    @param      outvid      output video
    @param      images      list of images to use in the video
    @param      fps         frame per second
    @param      size        size of each frame
    @param      format      see http://www.fourcc.org/codecs.php
    @return                 see http://opencv-python-tutroals.readthedocs.org/en/latest/py_tutorials/py_gui/py_video_display/py_video_display.html
 
    The function relies on http://opencv-python-tutroals.readthedocs.org/en/latest/.
    By default, the video will have the size of the first image.
    It will resize every image to this size before adding them to the video.
    '''
    logTrace ('Combining images into video', Precision.NORMAL)
    output = joinPaths(getTmpFolder(), outvid)
    from cv2 import VideoWriter, VideoWriter_fourcc, imread, resize
    fourcc = VideoWriter_fourcc(*format)
    vid = None
    for image in images:
        if not os.path.exists(image):
            raise FileNotFoundError(image)
        img = imread(image)
        if vid is None:
            if size is None:
                size = img.shape[1], img.shape[0]
            vid = VideoWriter(output, fourcc, float(fps), size)
        if size[0] != img.shape[1] and size[1] != img.shape[0]:
            img = resize(img, size)
        vid.write(img)
    vid.release()
    return vid
