# User Manual
## __Back End and Physical Setup__:
#### Image the Raspberry Pi:
•	The official guide for this process can be found here: https://www.raspberrypi.org/documentation/installation/installing-images/
•	For the purposes of this generation of the product, our team used Raspbian GNU / Linux 9, also known as Stretch, but the OS version for the system should have little influence on proper operation

#### Connect the Pi to basic peripherals and boot:
•	Connect mouse and keyboard via USB
•	Connect HDMI cable to external monitor
•	Connect Ethernet cable for wired network connection (optional, only needed for setup)
•	Connect the Pi to wall power adapter
•	Boot into Raspbian or preferred OS

#### Enable system interfaces:
•	Once booted in, click on the Raspberry Pi symbol to open the system menu
•	Navigate down to “Preferences” and open the “Raspberry Pi Configuration” tab
•	Navigate to the “Interfaces” tab and ensure that Camera, SSH, VNC, and I2C are enabled

#### Setup remote monitoring webserver on the Pi:
•	Pagekite is used to assign hostnames to outward facing VNC addresses to make remote monitoring possible from anywhere
•	Sign up for Pagekite here: https://pagekite.net/signup/
•	Follow the guide at the following page: https://pagekite.net/support/quickstart/
•	Once initial setup is completed, two kites should be added by executing the following from command line:
  o	“python2 pagekite.py --add 80 <site_name>.pagekite.me”
  o	“python2 pagekite.py --add 5900 raw:vnc.<site_name>.pagekite.me:5900”
•	Both of these hostnames need to be up at all times and, after their creation, can be launched using the following from command line:
  o	“python2 pagekite.py 80 <site_name>.pagekite.me”
  o	“python2 pagekite.py port# raw:vnc.<site_name>.pagekite.me:5900”
•	This application’s website contains instructions on how to run this program from startup, if desired

#### Setup VNC monitoring on remote machine:
•	Download VNC Viewer by RealVNC on the machine the Pi will be monitored from
•	Navigate to preferences and locate the “Proxy” tab
•	Select the options to “Use these proxy settings”
•	Enter the following values:
  o	Server: vnc.<site_name>.pagekite.me:443
  o	Type: HTTP Connect
  o	User / Pass: pi / raspberry (initial image user / pass)
•	You can then connect via VNC to the Pi via the address vnc.<site_name>.pagekite.me:5900

#### Share SSH keys between the Pi and data server:
•	From the Raspberry Pi, generate an SSH key by executing the following on command line: 
  o	“ssh-keygen”
•	Then copy this key to the remote data server by executing the following: 
  o	“ssh-copy-id –i ~/.ssh/id_rsa.pub <X.X.X.X>”
•	This step is absolutely vital for this application’s performance and can be tested by attempting to SSH to the remote data server without password:
  o	“ssh <X.X.X.X>”

#### Setup Redis-Server on the Pi:
•	Redis-Server is used implement a job queuing process processing data from the application
•	The setup process can be found at the following: https://habilisbest.com/install-redis-on-your-raspberrypi
•	Once Redis is properly setup, this queue webserver should be run constantly when data is being processed by doing the following from command line:
  o	“redis-server”

#### Setup SQL Server on data server:
•	Both SQL Server and the SQL Command Line Tools should be installed on the data server
•	The following process should be followed:
  o	https://docs.microsoft.com/en-us/sql/linux/quickstart-install-connect-ubuntu?view=sql-server-ver15
  o	Please note, an Ubuntu based server is currently deployed for this group, but Microsoft provides installation guides for these tools for most common operating systems
•	Once SQL Server is properly setup, a table with the following columns and data types should be created (Please note: currently, all variables are VARCHAR type)
  o	Timestamp – VARCHAR
  o	pH – FLOAT
  o	Conductivity – FLOAT
  o	Temperature – FLOAT
  o	Humidity – FLOAT
  o	Image Name – VARCHAR

#### Setup ImageMagick on data server (optional):
•	ImageMagick can be used to view images via X server when a machine establishes an SSH connection with the data server
•	The following shows the setup process for a typical Ubuntu machine: https://linuxconfig.org/how-to-install-imagemagick-7-on-ubuntu-18-04-linux
•	In order to launch the X server on startup of the SSH session, simply type the following when first connecting:
  o	“ssh <user>@<X.X.X.X> -X”
•	Then, in order to display any image type the following on command line, once inside the image’s directory:
  o	“display <filename>.<extension>”
•	If continual issues occur with displaying images, make sure the $DISPLAY environment variable is set correctly on your data server by executing the following:
  o	“export DISPLAY=localhost:0.0”

#### Setup full peripherals:
•	Connect the PiCamera via GPIO ribbon the Pi’s camera port
•	Connect the Atlas T3 Tentacle hat to the Pi’s GPIO header and attach the appropriate Atlas sensors to their respective serial cable header
•	Attach the GPIO ribbon cable to the T3’s GPIO header extension, then connect a breadboard on the ribbon cable
•	Connect all additional sensors to their respective GPIO ports on the ribbon cable’s breadboard connector
•	Attach battery powering system, lower device into enclosure and properly attach sensors and camera to arms

#### Download application package from Github:
•	Download full application (3 scripts) from Github and create an appropriate environment for them (i.e. create and name a folder solely for holding the scripts)
•	Establish a folder called “capstone” on the Pi’s desktop, which will be used for storing the processed data and images

#### Download Python packages for scripts:
•	Execute the following from the command line to install a Python package:
  o	“pip install <pkg_name>”
•	The following is a list and description of all Python packages needed to run this application:
  o	time – Used to implement wait periods, timings
  o	sys – Used to force clean exit from script on error outs
  o	OS – Used to execute CMD commands from inside script
  o	subprocess – Used to call CMD subprocesses from inside script (i.e. rsync calls)
  o	picamera – Used to operate and manipulate Pi camera
  o	datetime – Used to establish time stamped naming conventions
  o	RPi.GPIO – Used to operate Pi GPIO ports
  o	Adafruit_DHT – Used to gather temperature and humidity data from Adafruit DHT11 or DHT22 sensor
  o	IO – Used to create and implement filestreams
  o	fcntl – Used to interact with I2C parameters for Atlas sensors
  o	string – Used to interact with and manipulate strings
  o	copy – Used to move I2C parameters between addresses by copying values under certain specified conditions
  o	RQ – Used to simply implement a Redis job queue (note: this is unofficial)
  o	Redis – Used to connect to Redis queue from inside script (note: this is official)
  o	Pyodc – Used to setup script connection to SQL Server 

#### Edit variable information in scripts:
• atlas.py – queue name for Redis queue, username and IP for data server, rsync folder name on data server
•	atlas_upload.py – queue name for Redis queue, connection details for SQL Server on data server, schema and table names for SQL Server table

#### Script details:
•	atlas.py:
  o	Takes sensor readings and images, submits data to Redis queue and uploads CSV and images to directory on data server
  o	Run at user’s discretion (i.e. run when user wants to run an experiment)
  o	Execute with the following: “python atlas.py”
•	atlas_worker.py:
  o	Acts as middleman and takes enqueued data to be submitted to queue and pushed to the correct script
  o	This script can be left running at all times due to low CPU and memory impact, as it will process results any time they are submitted
  o	Execute with the following: “python atlas_worker.py <queue_name>”
•	atlas_upload.py:
  o	Uploads the queued data to the remote data server’s SQL Server table
  o	NEVER interacted with by the user, this script is only used when called from the main atlas.py

## __System Operational Notes__:
•	Python version to be used – 2.7.13
  o	Though Python 2.7 is going to be considered fully deprecated soon, the only way that the current build works with Atlas’ provided I2C software is if it is used
  o	NOTE: ensure that the relevant version of Pip is deployed for installing packages for the correct version of Python
•	Constantly running scripts
  o	The easiest way to implement the technologies discussed in this guide without too much maintenance is to have several scripts     continually run (or to add them to your Bash configuration for launch on startup)
  o	It is recommended that both Pagekite addresses (main and VNC), atlas_upload, and redis-server stay continually running
•	This enables the application to run with end-to-end success by only executing the main atlas.py

## __Front End Setup__:
•	This project is uses a React front end app that is written in JavaScript.
•	Currently the code can be seen on a front-end GUI. However, due to some impediments related to the Coronavirus it is very basic and there is no user experience.
•	Information and documentation for React can be found here: https://reactjs.org/
•	The connection to the front-end is made in the Index.js file
•	To setup the environment for into the terminal and run the following:
  o	mkdir “folder name”
  o	touch package.json
  o	npm init -y
• Insert the code into the index.js file
• Install the following packages:
  o	yarn add express 
  o yard add mysql 
  o	yarn add cors
  o	yarn add react
•	In order to run the front end code, run the following command: ‘nodemon Index.js’
• Ensure that you are in the correct folder when running the code
