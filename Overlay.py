from gpiozero import Button
import RPi.GPIO as GPIO
from time import sleep
import picamera
from picamera import PiCamera
from datetime import datetime
from signal import pause
import os
import serial
import numpy as np
import string
from PIL import Image, ImageDraw, ImageFont
import json

# changing variables based on raspi
path = '/media/usb3/'  # usb path to save files
serialPiPort = '/dev/ttyACM0'
imagePath = "/home/pi/Desktop/vision/"  # images path on pi

# setup display variables
screenX = int(1280)
screenY = int(720)  # camera is also recording at this res
screenFramrate = 30
linegap = int(0.04 * screenY)
linewidth = int(0.01 * screenY)
sliderwidth = int(0.02 * screenY)
lineextra = int(0.05 * screenY)
barcolor = (26, 255, 26, 230)
slidercolor = (153, 102, 255, 230)
background = (0, 0, 0, 80)
yawRange = int(90)
pitchRange = int(30)
buttonPinNum = 2  # GPIO 2, PIN 3

# initial data values (pre serial)
jsonLine = {'yaw': 20, 'pitch': 10, 'rpm': '100', 'speed': '2', 'depth': '2.5', 'battery': True}

# camera Setup
camera = PiCamera()
camera.led = True
camera.resolution = (screenX, screenY)
camera.framerate = screenFramrate
camera.vflip = True
camera.clock_mode = 'reset'


# serial setup
class DataLine:
	def __init__(self, jsonLine):
		self.yaw = jsonLine['yaw']
		self.pitch = jsonLine['pitch']
		self.rpm = jsonLine['rpm']
		self.speed = jsonLine['speed']
		self.depth = jsonLine['depth']
		self.battery = jsonLine['battery']


print("Serial Setup")
ending = bytes('}', 'utf-8')
ser = serial.Serial(
	port='/dev/ttyACM0',
	baudrate=9600
	#    parity=serial.PARITY_NONE,
	#    stopbits=serial.STOPBITS_ONE,
	#    bytesize=serial.EIGHTBITS,
	#    timeout=1
)

# creating blank image canvas and fonts data
blankCanvas = Image.new('RGBA', (screenX, screenY))

datafont = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 20)
smalltextfont = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 8)

# creaitng images for indicators
WarningIM = Image.open(imagePath + "warning.png")
WarningIM = WarningIM.resize([linegap * 2, linegap * 2])
BatteryIM = Image.open(imagePath + "lowbatt.png")
BatteryIM = BatteryIM.resize([linegap * 2, linegap * 2])
RaceIM = Image.open(imagePath + "sub.png")
RaceIM = RaceIM.resize([linegap * 2, linegap * 2])
lightsIM = Image.open(imagePath + "highbeams.png")
lightsIM = lightsIM.resize([linegap * 2, linegap * 2])


# Effect: Create stationary image for bars/backgrounds on overlay then adds overlay to camera
def paintStationaryOverlay():
	pitchYawAxisIM = Image.new('RGBA', (screenX, screenY))
	draw = ImageDraw.Draw(pitchYawAxisIM)
	draw.rectangle([0, 0, screenX, linegap * 2.5], fill=background)
	draw.rectangle([screenX - linegap * 2.5, 0, screenX, screenY], fill=background)
	draw.rectangle([screenX * 0, screenY - linegap * 2, screenX * 1, screenY], fill=background)
	draw.line([linegap + lineextra, linegap, screenX - (linegap + lineextra), linegap], fill=barcolor, width=linewidth)
	draw.line([screenX - (linegap), linegap + lineextra, screenX - (linegap), screenY - linegap - lineextra],
			  fill=barcolor, width=linewidth)
	draw.line([screenX / 2, linegap * 0.5, screenX / 2, linegap * 1.5], fill=barcolor, width=linewidth)
	draw.line([screenX - linegap * 1.5, screenY / 2, screenX - linegap * 0.5, screenY / 2], fill=barcolor,
			  width=linewidth)
	draw.text([screenX * 0.5 - 8 * 1, linegap * 2], "yaw", fill=barcolor, font=smalltextfont)
	draw.text([screenX - linegap * 2, screenY * 0.5 - 9 * 2], "p", font=smalltextfont, fill=barcolor)
	draw.text([screenX - linegap * 2, screenY * 0.5 - 9 * 1], "i", font=smalltextfont, fill=barcolor)
	draw.text([screenX - linegap * 2, screenY * 0.5], "t", font=smalltextfont, fill=barcolor)
	draw.text([screenX - linegap * 2, screenY * 0.5 + 9], "c", font=smalltextfont, fill=barcolor)
	draw.text([screenX - linegap * 2, screenY * 0.5 + 9 * 2], "h", font=smalltextfont, fill=barcolor)
	draw.text([screenX - linegap * 2, linegap * 2], str(pitchRange), font=smalltextfont, fill=barcolor)
	draw.text([screenX - linegap * 2, screenY - linegap * 2], "-" + str(pitchRange), font=smalltextfont, fill=barcolor)

	camera.add_overlay(pitchYawAxisIM.tobytes(), layer=3)


# Effect: Reads serial data and returns a python class object of the data
def readSerialData():
	ending = bytes('}', 'utf-8')
	line = ser.read_until(ending)
	try:
		jsonLine = json.loads(line)
		# print(jsonLine)
		try:
			global dataLine
			dataLine = DataLine(jsonLine)
			return dataLine
		except KeyError:
			print("KeyError", "Dictionary key incorrect from serial data")
	# print(dataLine.__dict__)
	except json.decoder.JSONDecodeError:
		print("json.decoder.JSONDecodeError")
	except UnicodeDecodeError:
		print("UnicodeDecodeError")


# Effect: Creates moving indicators on bars on overlay then adds overlay to camera
def paintMovingDisplay(dataLine):
	# configure data Values to display
	ValuesText = "RPM:" + str(dataLine.rpm) + " rpm    Speed:" + str(
		dataLine.speed) + " m/s     Depth:" + str(dataLine.depth) + "m"
	pitchAjust = (dataLine.pitch + pitchRange) / (pitchRange * 2)
	yawAjust = (dataLine.yaw + yawRange) / (yawRange * 2)

	# creating changing data images for serial canvas
	movingIM = Image.new('RGBA', (screenX, screenY))
	draw = ImageDraw.Draw(movingIM)
	draw.line([yawAjust * screenX, linegap * 0.5, yawAjust * screenX, linegap * 1.5], fill=slidercolor,
			  width=sliderwidth)
	draw.line([screenX - linegap * 1.5, screenY * pitchAjust, screenX - linegap * 0.5, screenY * pitchAjust],
			  fill=slidercolor, width=sliderwidth)
	draw.text([screenX * 0.3, screenY - linegap * 1.5], ValuesText, fill=slidercolor, font=datafont, alin="center")
	# if DataToDisplay['warning'] == True:
	# movingIM.paste(WarningIM,[int(linegap*2),int(screenY-2*linegap)])
	if dataLine.battery == True:
		movingIM.paste(BatteryIM, [int(linegap * 4), int(screenY - 2 * linegap)])

	# update the overlay with the new image

	global movingOverlay
	global movingOverlayPrev

	# 1. New overlay is added and reference is held
	movingOverlay = camera.add_overlay(movingIM.tobytes(), layer=4)

	# 2. Previous overlay is removed
	if movingOverlayPrev is None:
		print("Prev is None")
	else:
		camera.remove_overlay(movingOverlayPrev)

	# 3. Current overlay is set as the Previous overlay
	movingOverlayPrev = movingOverlay


# Previous .update method
# movingOverlay.update(movingIM.tobytes())

# Button Setup
buttonStatus = Button(buttonPinNum)

# Record

SAVE_FILE_PATH = '/media/usb3/recordedOverlayVideos'


def cameraRecordStart():
	create_directory()
	camera.start_recording(SAVE_FILE_PATH + "/Video.h264")


def cameraRecordStopAndSave():
	camera.stop_recording()


def create_directory():
	PATH = SAVE_FILE_PATH

	if os.path.exists(PATH):
		print("File directory exists")
	else:
		print("File director does not exist, Attempting to create directory")
		try:
			os.mkdir(PATH)
		except OSError:
			print("Creation of the directory %s failed" % PATH)
		else:
			print("Successfully created the directory %s " % PATH)


print("Start Serial Read")
camera.start_preview()
paintStationaryOverlay()

cameraRecordStart()

movingOverlayPrev = None
# Grabs the static json
dataLine = DataLine(jsonLine)
while True:

	while True:
		try:
			dataLine = readSerialData()
			# need to invoke to trigger possible AttributeError
			dataLine.__dict__
			break
		except AttributeError:
			print("AttributeError")
	# print to check values of each line
	print(dataLine.__dict__)
	textString = dataLine.__dict__
	print(str(textString))
	camera.annotate_text = str(textString)
	paintMovingDisplay(dataLine)

	print("Button Status is: ", buttonStatus.value)
	if buttonStatus.value == 1:
		print("button pressed")

		cameraRecordStopAndSave()
		break
