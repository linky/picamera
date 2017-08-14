#!/usr/bin/python3

import os
import sh
import sys
import glob
import picamera

VIDEO_DIR = '/mnt'
FORMAT = 'mp4'
RESOLUTION = (640, 360)
FPS = 24
VIDEO_LENGTH = 15 # min

def getUsbDrive():
	partitionsFile = open("/proc/partitions")
	lines = partitionsFile.readlines()[2:]
	for line in lines:
		words = [x.strip() for x in line.split()]
		minor_number = int(words[1])
		device_name = words[3]
		if minor_number % 16 == 0:
			path = "/sys/class/block/" + device_name
		if os.path.islink(path):
			if os.path.realpath(path).find("/usb") > 0:
				print('/dev/' + device_name + '1')
				return '/dev/' + device_name + '1'
	return None

def mountDrive():
	drivePath = getUsbDrive()
	print('mount %s' % drivePath)
	sh.mount(drivePath, VIDEO_DIR)

def umountDrive():
	print('umount %s' % VIDEO_DIR)
	sh.umount(VIDEO_DIR)

def genNewVideoPath():
	files = list(map(os.path.basename, glob.glob(VIDEO_DIR + '/*.' + FORMAT)))
	max_index = max([ int(f.split('.' + FORMAT)[0]) for f in files ])

	return str(max_index + 1) + '.' + FORMAT

def getOldVideoPath():
	files = glob.glob(VIDEO_DIR + '/*.mp4')
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
		print('start writing %s' % filename)
		# check if avaliable space on sdcard < 80%
		used_ratio = getDriveUsedRatio()
		print('sdcard space available: %f%%' % used_ratio)
		while used_ratio > 0.8: 
			old_video = getOldVideoPath()
			os.remove(old_video)
			used_ratio = getDriveUsedRatio()

		camera.wait_recording(VIDEO_LENGTH*60) # 15 min

def setAutostart():
	self_path = os.path.realpath(__file__)
	print('set autostart %s' % self_path)
	with open('/etc/rc.local') as fin:
		with open('/etc/rc.local.tmp') as fout:
			while line in fin:
				if line == 'exit 0':
					fout.write(self_path + ' &\n')
				fout.write(line)

	os.rename('/etc/rc.local', '/etc/rc.local.old')
	os.rename('/etc/rc.loca.tmp', '/etc/rc.local')


#######################################################################

# autostart
if len(sys.argv) == 2 and sys.argv[1] == '-a':
	print('set autostart')
	setAutostart()

# check sdcard
while True:
	print('check sdcard')
	if not getUsbDrive():
		os.sleep(3)
		continue

# processing
try:
	mountDrive()

	writeVideo();

except Exception as e:
	print(e)
finally:
	umountDrive()
