"""
POP Final Version - ECE 3915W Spring 2019
Connor Kraft, Phillip Jones, Rachel Zaltz

The following takes images and sensor data at
specified time intervals, then transfers the images
and data log wirelessly

Please do the following from your Raspberry Pi's
command line, in order for password-less entry
to function properly (x.x.x.x - destination IP):

'user$ ssh-keygen'
'user$ ssh-copy-id -i ~/.ssh/id_rsa.pub x.x.x.x'

Note - this method requires the remote host's password
to be entered once on the command line of the pi, then
saves a keyset for repeated, any-time access by SSH

You can test password-less auth with the following:

'user$ ssh x.x.x.x'
"""
from time import sleep
import sys
import os  # Enables user to act on files outside program
import subprocess  # Use to invoke call to cmd
import picamera
import datetime
import RPi.GPIO as GPIO  # Use to interact with RPi GPIO pins
import Adafruit_DHT  # Stock module for temp/humidity sensor

# Camera init
camera = picamera.PiCamera()
camera.resolution = '1080p'

# Pin init
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(21, GPIO.OUT)

# Sensor init
sensor = Adafruit_DHT.DHT11
pin = 23


def main():
    # Clear out folder holding pics / data before each run
    os.system('rm -rf /home/pi/test/*')
    # Timestamp name of data log file and enable write
    d2 = datetime.datetime.now()
    file = open('/home/pi/test/' + d2.strftime('%Y.%m.%d-%H.%M.%S') + '.txt', 'w')
    try:
        camera.start_preview(fullscreen=False, window=(650, 7, 1100, 1100))
        # i denotes number of pictures being taken
        # 'sleep' times denote intervals of image capture / data log
        """
        - Establishes timestamped naming convention for image files
        - Turns on 'flash', captures and saves image, turns off 'flash'
        - Captures temp / humidity data from DHT 11 sensor
        - Writes said data to txt file w/ timestamps
        """
        for i in range(0, 10):
            d = datetime.datetime.now()
            print(d)
            pict = d.strftime('%Y.%m.%d-%H.%M.%S')
            picn = ('/home/pi/test/' + pict + '.jpg')
            print('Light on\t')
            GPIO.output(21, GPIO.HIGH)
            sleep(0.5)
            print('Taking picture\t')
            camera.capture(picn)
            print('Light off, taking sensor data\n')
            GPIO.output(21, GPIO.LOW)
            humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
            file.write('Time:' + d.strftime('%Y.%m.%d-%H.%M.%S\t'))
            file.write('Temperature:' + str(temperature) + 'deg C\t')
            file.write('Humidity:' + str(humidity) + '%\n')
            sleep(2)
            continue

    # Proper exit: close camera, file, and invoke cmd to employ SSH file sync
    camera.stop_preview()
    file.close()
    subprocess.call(['rsync', '-avrPzh', '/home/pi/test/', '-e', 'ssh -p 22', 'User@x.x.x.x:~/Desktop/test'])
    sys.exit()

    # Improper exit: close camera, file, and brute force exit system
    except KeyboardInterrupt:
    camera.stop_preview()
    file.close()
    print('\nClosed by keyboard interrupt.')
    sys.exit()

if __name__ == '__main__':
    main()

