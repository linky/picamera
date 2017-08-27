#!/usr/bin/python3

import os
import sh
import sys
import glob
#import picamera
from time import sleep

VIDEO_DIR = '/mnt/'
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
	try:
		sh.umount(VIDEO_DIR)
	except Exception:
		pass

def genNewVideoPath():
	files = list(map(os.path.basename, glob.glob(VIDEO_DIR + '*.' + FORMAT)))
	max_index = max([ int(f.split('.' + FORMAT)[0]) for f in files ])

	#return str(max_index + 1) + '.' + FORMAT
	return max_index + 1

def getOldVideoPath():
	files = glob.glob(VIDEO_DIR + '/*.mp4')
	if not files:
		return None
	oldest_path = min(files, key=os.path.getctime)
	oldest_filename = os.path.basename(oldest_path)

	return VIDEO_DIR + oldest_filename


def getDriveUsedRatio():
	statvfs = os.statvfs(VIDEO_DIR)
	free = statvfs.f_frsize * statvfs.f_bavail
	used = statvfs.f_frsize * statvfs.f_blocks - free
	all = free + used
	print('free %d used %d' % (free, used))

	return (all - free)/all*100.0

def writeVideo():
#   camera = picamera.PiCamera()
#   camera.resolution = RESOLUTION
#   camera.framerate = FPS

    # write 15-minutes parts of stream
    #for filename in camera.record_sequence([VIDEO_DIR + str(genNewVideoPath() + part) + '.' + FORMAT for part in range(999)], format='h264', quality=23):
    for i in range(10000000):
        try:
            print('start writing %d' % i)
            # check if avaliable space on sdcard < 80%
            used_ratio = getDriveUsedRatio()
            print('sdcard used space: %.1f%%' % used_ratio)
            while used_ratio > 80:
                old_video = getOldVideoPath()
                print('removing old video file %s' % old_video)
                os.remove(old_video)
                used_ratio = getDriveUsedRatio()
            print('wait recording')
            f = open('/mnt/' + str(i) + '.mp4', 'w')
            for j in range(100000):
                f.write('asdsa' + str(j))
            sleep(1)
			
            #camera.wait_recording(VIDEO_LENGTH*60) # 15 min
        except Exception as e:
            print(e)
            umountDrive()
            while True:
                print('waiting USB-drive')
                if getUsbDrive():
                    break;
                sleep(3)
            mountDrive()



def setAutostart():
	self_path = os.path.realpath(__file__)
	os.system('cp %s /etc/init.d' % self_path)
	os.system('update-rc.d camera.py defaults')

#######################################################################

# autostart
if len(sys.argv) == 2 and sys.argv[1] == '-a':
	print('set autostart')
	setAutostart()
	sys.exit(0)

# check sdcard
while True:
	print('waiting USB-drive')
	if getUsbDrive():
		break;
	sleep(3)

# processing
try:
	mountDrive()

	writeVideo();

except Exception as e:
	print(e)
	print('but write video')
	writeVideo();
finally:
	umountDrive()
