#!/usr/bin/python3

import os
import sh
import glob

VIDEO_DIR = '/mnt'
FORMAT = 'mp4'

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
	return ""

def mountDrive():
	drivePath = getUsbDrive()
	sh.mount(drivePath, VIDEO_DIR)

def umountDrive():
	sh.umount(VIDEO_DIR)

def genNewVideoPath():
	files = list(map(os.path.basename, glob.glob(VIDEO_DIR + '/*.mp4')))
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


mountDrive()

new = genNewVideoPath();
print(new)
old = getOldVideoPath()
print(old)
used = getDriveUsedRatio()
print(used)

umountDrive()
