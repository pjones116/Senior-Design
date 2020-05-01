'''
ECE4925W - Final Capstone Submission, Spring 2020
Phillip Jones, Connor Kraft, Rachel Zaltz

final_atlas - takes data, organizes storage structure, submits queue request for transportation to storage server
final_atlas_worker - takes resulting data and actually submits to queue
final_atlas_upload - submits data to sql database on storage server

For detailed questions on packages used / scripts, please see User Manual Appendix and the FPR, in general

All information in Class AtlasI2C was taken from Atlas Scientific's sample program for I2C device communication
'''


from atlas_upload import upload_to_db       # Called script from our application package
import time                                 # Use for actual timing
from time import sleep                      # Use to stop scripts for period of time
import sys                                  # Use to control system level exit of program
import os                                   # Enables user to act on files outside program
import subprocess                           # Use to invoke call to cmd
import picamera                             # Use to control RPi camera
import datetime                             # Use to get current datetime info
import RPi.GPIO as GPIO                     # Use to interact with RPi GPIO pins
import Adafruit_DHT                         # Stock module for temp/humidity sensor
import io                                   # Use to create file streams
from io import open                         # Use to open files in file streams
import fcntl                                # Use to access I2C parameters
import string                               # Use to parse strings
import copy                                 # Use to implement copy as function of Python
from rq import Queue                        # Allows for Redis job queueing
from rq import get_current_job              # Use for getting information about current job
from redis import Redis                     # Use to make connection to Redis server
import psutil                               # Use to produce system level diagnostic info about RPi

# Open camera, set resolution
camera = picamera.PiCamera()
camera.resolution = '1080p'

# Open GPIO pin 21, set for output as "flash" for photo
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(21,GPIO.OUT)

# Initialize temp/hum sensor
sensor  = Adafruit_DHT.DHT11
pin = 23

# Initialize queue, open connection to atlas queue
redis_conn = Redis()
q = Queue('atlas', connection=redis_conn, default_timeout=300)

'''
All information in AtlasI2C is taken from the provided configuration of Atlas' I2C devices

This information can be altered as desired, please tread lightly when doing this,
as this can result in significant differences in operation for these sensors

In addition, this version has been altered, as the provided build encountered problems
with sensor configuration and operation
'''

class AtlasI2C:
    long_timeout = 1.5                      # Timeout needed to query readings / calibrations
    short_timeout = 0.3                     # Timeout for regular commands
    default_bus = 1                         # Default RPi I2C bus
    default_address = 98                    # Default sensor address
    LONG_TIMEOUT_COMMANDS = ("R", "CAL")    # Wait for long period while reading
    SLEEP_COMMANDS = ("SLEEP", )            # Assign sleep commands
    
    def __init__(self, address = default_address, bus = default_bus):
        # Init 2 file streams, for reading and writing
        self._address = address or self.default_address
        self.bus = bus or self.default_bus
        self._long_timeout = self.long_timeout
        self._short_timeout = self.short_timeout
        self.file_read = io.open(file="/dev/i2c-{}".format(self.bus), mode="rb", buffering=0)
        self.file_write = io.open(file="/dev/i2c-{}".format(self.bus), mode="wb", buffering=0)
        self.name = ""
    
    def set_i2c_address(self, addr):
        # Set I2C communications to slave address
        I2C_SLAVE = 0x703
        fcntl.ioctl(self.file_read, I2C_SLAVE, addr)
        fcntl.ioctl(self.file_write, I2C_SLAVE, addr)
        self.address = addr
    
    def write(self, cmd):
        # Appends null character and send string over I2C
        cmd += "\00"
        self.file_write.write(cmd.encode('latin-1'))

    def handle_raspi_glitch(self, response):
        if self.app_using_python_two():
            return list(map(lambda x: chr(ord(x) & ~0x80), list(response)))
        else:
            return list(map(lambda x: chr(x & ~0x80), list(response[1:])))

    def app_using_python_two(self):
        return sys.version_info[0] < 3

    def get_response(self, raw_data):
        if self.app_using_python_two():
            response = [i for i in raw_data if i != '\x00' ]
        else:
            response = raw_data

        return response

    def response_valid(self, response):
        valid = True
        error_code = None
        if(len(response)>0):
            if self.app_using_python_two():
                error_code = str(ord(response[0]))
            else:
                error_code = str(response[0])

            if error_code != '1':
                valid = False

        return valid, error_code

    def get_device_info(self):
        if(self.name == ""):
            return str(self.address)
        else:
            return str(self.address) + " " + self.name

    def read(self, num_of_bytes=31):
        raw_data = self.file_read.read(num_of_bytes)
        response = self.get_response(raw_data=raw_data)
        is_valid, error_code = self.response_valid(response=response)

        if is_valid:
            char_list = self.handle_raspi_glitch(response[1:])
            result = "Success " + self.get_device_info() + ": " + str(''.join(char_list))
        else:
            result = "Error " + self.get_device_info() + ": " + error_code

        return result

    def get_command_timeout(self, command):
        timeout = None
        if command.upper().startswith(self.LONG_TIMEOUT_COMMANDS):
            timeout = self._long_timeout
        elif not command.upper().startswith(self.SLEEP_COMMANDS):
            timeout = self.short_timeout

        return timeout

    def query(self, command):
        self.write(command)
        current_timeout = self.get_command_timeout(command=command)
        if not current_timeout:
            return "sleep mode"
        else:
            time.sleep(current_timeout)
            return self.read()

    def close(self):
        self.file_read.close()
        self.file_write.close()

    def list_i2c_devices(self):
        prev_addr = copy.deepcopy(self._address)
        i2c_devices = []
        for i in range(0,128):
            try:
                self.set_i2c_address(i)
                self.read(i)
                i2c_devices.append(i)
            except IOError:
                pass
        self.set_i2c_address(prev_addr)

        return i2c_devices

def main():
    # Allow for user input of experiment name
    # MUST BE IN QUOTES, NO SPACES
    experiment_name = input("Input the name of the experiment: ")
    # Timestamp name of data log file and enable write
    d2 = datetime.datetime.now()
    # Create local data dump folder
    os.system('mkdir /home/pi/Desktop/capstone/' + experiment_name + '.' + d2.strftime('%Y.%m.%d-%H.%M.%S'))
    # Create local data dump csv
    csv = open('/home/pi/Desktop/capstone/'+ experiment_name + '.'+ d2.strftime('%Y.%m.%d-%H.%M.%S') + '/' + d2.strftime('%Y.%m.%d-%H.%M.%S') +'.csv', 'a')
    # Create I2C port object
    device = AtlasI2C()
    try:
        # FOR LOOP HARD CODED, CHANGE IN FUTURE (NUMBER OF READS)
        # This loop turns on/off flash, takes photo in between, reads from each sensor
        # Sensor info and system diagnostics are then organized and submitted to the Redis queue for storage server
        # All info is then also saved to a local CSV, to be also transferred to storage server via rsync
        for i in range(0,5):
            d = datetime.datetime.now()
            print('\n')
            print(d)
            pict = d.strftime('%Y.%m.%d-%H.%M.%S')
            picn = ('/home/pi/Desktop/capstone/' + experiment_name + '.'+ d2.strftime('%Y.%m.%d-%H.%M.%S') + '/' + pict + '.png')
            print('Light on\t')
            GPIO.output(21,GPIO.HIGH)
            sleep(0.5)
            print('Taking picture\t')
            camera.capture(picn)
            print('Light off, taking sensor data')
            GPIO.output(21,GPIO.LOW)
            #humidity, temperature = Adafruit_DHT.read_retry(sensor,pin)
            # CHANGE THESE TEMP/HUM HARD CODED VALUES IN FUTURE
            temperature = 1.00
            humidity = 2.00
            device.set_i2c_address(99)
            phstring = device.query('R')[11:]
            phstring = str(phstring)
            device.set_i2c_address(100)
            condstring = device.query('R')[12:]
            condstring = str(condstring)

            data = {
                    'time' : d.strftime('%Y-%m-%d %H:%M:%S'),
                    'pH': phstring,
                    'conductivity': condstring,
                    'temperature': temperature,
                    'humidity': humidity,
                    'exp_name': experiment_name
                    }
            log_data = {
                    'CPU usage' : psutil.cpu_percent(),
                    'CPU temp' : subprocess.check_output(['vcgencmd', 'measure_temp'], stderr=subprocess.STDOUT),
                    'RAM usage' : psutil.virtual_memory()[2]
                    }
            job = q.enqueue(upload_to_db, data, result_ttl=86400)
            print('Current job on queue: %s\n' % (job.id,))
            # Parsing and handling this information is both annoying and difficult,
            # I reccomend leaving this scheme for the entirety of the project
            # i.e. I reccomend not moving away from CSV as a secondary storage method
            csv.write(unicode('experiment: ' + str(data['exp_name']) + ','))
            csv.write(unicode('time:  ' + str(data['time']) + ','))
            csv.write(unicode('pH:  ' + str(data['pH']) + ','))
            csv.write(unicode('conductivity:  ' + str(data['conductivity']) + ','))
            csv.write(unicode('temperaure:  ' + str(data['temperature']) + ','))
            csv.write(unicode('humidity:  ' + str(data['humidity']) + ',\n'))
            csv.write(unicode('CPU usage:  ' + str(log_data['CPU usage']) + ','))
            csv.write(unicode('CPU ' + str(log_data['CPU temp'])[:-1] + ','))
            csv.write(unicode('RAM usage:  ' + str(log_data['RAM usage']) + ','))
            csv.write(unicode('\n\n'))
            sleep(3)
            continue
        
        # Proper exit: close camera, file, and invoke cmd to employ SSH file sync
        # Then exit at a system level
        camera.stop_preview()
        csv.close()
        subprocess.call(['rsync','-avrPzh','/home/pi/Desktop/capstone','-e','ssh -p 22','user@X.X.X.X:~/'])
        sys.exit()
    
    # Improper exit: close camera, file, and brute force exit system
    except KeyboardInterrupt:
        camera.stop_preview()
        csv.close()
        print('\nClosed by keyboard interrupt.')
        sys.exit()

if __name__ == '__main__':
    main()



