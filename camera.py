#!/usr/bin/python3

import os
import sh
import glob
import picamera

VIDEO_DIR = '/mnt'
FORMAT = 'mp4'
RESOLUTION = (640, 360)
FPS = 24
VIDEO_LENGTH = 15 # min

def getUsbDrive():
	partitionsFile = open("/proc/partitions")
	lines = partitionsFile.readlines()[2:]#Skips the header lines
	for line in lines:
		words = [x.strip() for x in line.split()]
		minorNumber = int(words[1])
		deviceName = words[3]
		if minorNumber % 16 == 0:
			path = "/sys/class/block/" + deviceName
		if os.path.islink(path):
			if os.path.realpath(path).find("/usb") > 0:
				return "/dev/" + deviceName + '1'
	return None

def mountDrive():
	drivePath = getUsbDrive()
	sh.mount(drivePath, VIDEO_DIR)

def umountDrive():
	sh.umount(VIDEO_DIR)

def genNewVideoPath():
	files = list(map(os.path.basename, glob.glob(VIDEO_DIR + '/*.' + FORMAT)))
	max_index = max([ int(f.split('.' + FORMAT)[0]) for f in files ])

	return str(max_index + 1) + '.' + FORMAT

def getOldVideoPath():
	files = glob.glob(VIDEO_DIR + '/*.mp4') # * means all if need specific format then *.csv
	oldest_path = min(files, key=os.path.getctime)
	oldest_filename = os.path.basename(oldest_path)

	return oldest_filename


def getDriveUsedRatio():
	statvfs = os.statvfs(VIDEO_DIR)
	free = statvfs.f_frsize * statvfs.f_bavail
	used = statvfs.f_frsize * statvfs.f_blocks - free

	return free/used

def writeVideo():
	camera = picamera.PiCamera()
	camera.resolution = RESOLUTION
	camera.framerate = FPS

	# write 15-minutes parts of stream
	for filename in camera.record_sequence(['%d.' + FORMAT % (part + 1) for part in range(999)]):
		camera.wait_recording(VIDEO_LENGTH*60) # 15 min


###############################3#


# check sdcard
while True:
	if not getUsbDrive():
		os.sleep(3)
		continue

# processing
try:
	mountDrive()

	# check if avaliable space on sdcard < 80%
	used_ratio = getDriveUsedRatio()
	while used_ratio > 0.8: 
		old_video = getOldVideoPath()
		os.remove(old_video)
		used_ratio = getDriveUsedRatio()

	writeVideo();

except Exception as e:
	print(e)
finally:
	umountDrive()
