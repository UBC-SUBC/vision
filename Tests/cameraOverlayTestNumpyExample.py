import time
import picamera
import numpy as np
import picamera
from PIL import Image, ImageDraw
from time import sleep
import datetime as dt

# Create an array representing a 1280x720 image of
# a cross through the center of the display. The shape of
# the array must be of the form (height, width, color)
a = np.zeros((720, 1280, 3), dtype=np.uint8)
a[360, :, :] = 0xff
a[:, 640, :] = 0xff

camera = picamera.PiCamera()
camera.resolution = (1280, 720)
camera.framerate = 24
camera.start_preview()
# Add the overlay directly into layer 3 with transparency;
# we can omit the size parameter of add_overlay as the
# size is the same as the camera's resolution
o = camera.add_overlay(a.tobytes(), layer=3, alpha=80)


background = (250,250,250,80)
screenX = int(1280)
screenY = int(720)
blankcanvas = Image.new('RGBA',(screenX,screenY), (255,255,255,50))
pitchYawAxisIM = blankcanvas
draw = ImageDraw.Draw(pitchYawAxisIM)
draw.rectangle([0,0,screenX,2*2.5],fill=background)
draw.ellipse((20, 20, 180, 180), fill = background, outline ='blue', width = 3)
draw.ellipse((20, 20, 180, 180), fill = background, outline ='blue')

stationaryoverlay = camera.add_overlay(pitchYawAxisIM.tobytes(),layer=5, format='rgba')


try:
    # Wait indefinitely until the user terminates the script
    while True:
        time.sleep(1)
finally:
    camera.remove_overlay(o)