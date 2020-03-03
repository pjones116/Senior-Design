from atlas_upload import upload_to_db
import time
from time import sleep
import sys
import os                   # Enables user to act on files outside program
import subprocess           # Use to invoke call to cmd
import picamera
import datetime
import RPi.GPIO as GPIO     # Use to interact with RPi GPIO pins
import Adafruit_DHT         # Stock module for temp/humidity sensor
import io                   # Use to create file streams
from io import open
import fcntl                # Use to access I2C parameters
import string               # Use to parse strings
import copy
from rq import Queue
from rq import get_current_job
from redis import Redis

# Camera init
camera = picamera.PiCamera()
camera.resolution = '1080p'

# Pin init
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(21,GPIO.OUT)

# Sensor init
sensor  = Adafruit_DHT.DHT11
pin = 23

# Queue
redis_conn = Redis()
q = Queue('atlas', connection=redis_conn, default_timeout=300)

class AtlasI2C:
    long_timeout = 1.5                  # Timeout needed to query readings / calibrations
    short_timeout = 0.3                 # Timeout for regular commands
    default_bus = 1                     # Default RPi I2C bus
    default_address = 98                # Default sensor address
    LONG_TIMEOUT_COMMANDS = ("R", "CAL")
    SLEEP_COMMANDS = ("SLEEP", )
    
    def __init__(self, address = default_address, bus = default_bus):
        # Init 2 file streams, for reading and writing
        self._address = address or self.default_address
        self.bus = bus or self.default_bus
        self._long_timeout = self.long_timeout
        self._short_timeout = self.short_timeout
        self.file_read = io.open(file="/dev/i2c-{}".format(self.bus), mode="rb", buffering=0)
        self.file_write = io.open(file="/dev/i2c-{}".format(self.bus), mode="wb", buffering=0)
        #self.set_i2c_address(self.address)
        self.name = ""
        #self._module = moduletype
        
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

    # Clear out folder holding pics / data before each run
    os.system('rm -rf /home/pi/Desktop/SeniorDesign/*')
    # Timestamp name of data log file and enable write
    d2 = datetime.datetime.now()
    #csv = open('/home/pi/Desktop/SeniorDesign/'+d2.strftime('%Y.%m.%d-%H.%M.%S')+'.csv','a')
    # Create I2C port object
    device = AtlasI2C()
    try:
        #camera.start_preview(fullscreen = False, window = (650,7,1100,1100))
        #info = string.split(device.query('I'), ',')[1]
        # i denotes number of pictures being taken
        # 'sleep' times denote intervals of image capture / data log
        '''
            - Establishes timestamped naming convention for image files
            - Turns on 'flash', captures and saves image, turns off 'flash'
            - Captures temp / humidity data from DHT 11 sensor
            - Writes said data to txt file w/ timestamps
            '''
        for i in range(0,10):
            d = datetime.datetime.now()
            print(d)
            pict = d.strftime('%Y.%m.%d-%H.%M.%S')
            picn = ('/home/pi/Desktop/SeniorDesign/'+pict +'.jpg')
            print('Light on\t')
            GPIO.output(21,GPIO.HIGH)
            sleep(0.5)
            print('Taking picture\t')
            camera.capture(picn)
            print('Light off, taking sensor data\n')
            GPIO.output(21,GPIO.LOW)
            #humidity, temperature = Adafruit_DHT.read_retry(sensor,pin)
            temperature = 1.00
            humidity = 2.00
            device.set_i2c_address(99)
            phstring = device.query('R')[11:]
            phstring = float(phstring)
            device.set_i2c_address(100)
            condstring = device.query('R')[12:]
            condstring = float(condstring)
            #imagesend = open(picn, 'rb').read()

            data = {
                    'time' : str(d.strftime('%Y-%m-%d %H:%M:%S')),
                    'pH': phstring,
                    'conductivity': condstring,
                    'temperature': temperature,
                    'humidity': humidity,
                    #'image': imagesend
                    }
            job = q.enqueue(upload_to_db, data, result_ttl=86400)
            print('Current job on queue: %s' % (job.id,))
            #csv.write('Time: ' + d.strftime('%Y.%m.%d-%H.%M.%S') + ',')
            #csv.write('pH: ' + phstring + ',')
            #csv.write('Conductivity: ' + condstring + ',')
            #csv.write('Temperature: ' + str(temperature)  + ' deg C' + ',')
            #csv.write('Humidity: ' + str(humidity) + ' %\n')
            sleep(2)
            continue
        
        # Proper exit: close camera, file, and invoke cmd to employ SSH file sync
        camera.stop_preview()
        #csv.close()
        print('All data and images uploaded to queue succesfully')
        #subprocess.call(['rsync','-avrPzh','/home/pi/Desktop/SeniorDesign','-e','ssh -p 22','User@x.x.x.x:~/Desktop/test'])
        sys.exit()
    
    # Improper exit: close camera, file, and brute force exit system
    except KeyboardInterrupt:
        camera.stop_preview()
        csv.close()
        print('\nClosed by keyboard interrupt.')
        sys.exit()

if __name__ == '__main__':
    main()



