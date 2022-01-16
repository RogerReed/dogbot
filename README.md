# Alexa Dog Feeder with AWS IoT
Check out the associated blog with this source repo for more detail on the build.
http://alexa-dog-feeder.blogspot.com/

## Development
### MacOS
```
brew install pipenv
pipenv shell
sudo python setup.py install
pipenv install
```
### Windows
```
choco install pipenv
pipenv shell
python setup.py install
pipenv install
```

## Raspberry Pi
### Pi Camera
See documentation for Python 2 https://picamera.readthedocs.io/en/release-1.10/install2.html
```
sudo apt update && sudo apt full-upgrade
sudo apt-get install python-picamera
```

### Neopixel Prep
Follow this tutorial to prep the OS, disable audio, and install the neopixel library to use PIN18 for signals as described https://tutorials-raspberrypi.com/connect-control-raspberry-pi-ws2812-rgb-led-strips/, specifically:
1. Update package sources:
```
sudo apt-get update
sudo apt-get install gcc make build-essential python-dev git scons swig python-pip
```
2. Deactivate audio port which conflicts with PWM needed for neopixels:
```
sudo vi /etc/modprobe.d/snd-blacklist.conf
```
and add this line
```
blacklist snd_bcm2835
```
3. Deactivating audio also requires updating the boot config:
```
sudo vi /boot/config.txt
```
and comment out this line
```
#dtparam=audio=on
```
4. Reboot:
```
sudo reboot
```
5. Download the library:
```
git clone https://github.com/jgarff/rpi_ws281x
```
6. Compile C files
```
cd rpi_ws281x/
sudo scons
```
7. Build and install python variant
```
cd python
sudo python setup.py build
sudo python setup.py install
```

### Deploy Python Code
1. SFTP files from this repo's *device* path to your Pi in */home/pi/dogbot* path (except any files you may have in place to mock GPIO or neopixel for local development)
2. From */home/pi/dogbot* path install requirements (with requirements.txt since pipenv isn't great on Raspberry Pi)

Note: Needs to be run as sudo, since dogbot.py runs as root for dev permissions needed by neopixel
```
sudo pip install -r requirements.txt
```
1. Ensure *device/certs* are included as referenced in code

### Sync Files During Development
Use the Visual Studio Code SFTP plugin (see .vscode/sftp.json configuration) to sync code to Raspberry Pi as you make changes.

## Install dogbot as Raspberry Pi Service Install
Copy dogbot.service to */lib/systemd/system/dogbot.service*
```
sudo systemctl daemon-reload
sudo systemctl enable dogbot.service
sudo systemctl start dogbot.service
```

## Install watchdog to ensure Pi reboots on network failure
1. Install watchdog
```
sudo apt-get install watchdog
```
2. Determine network interface you want to watch
```
ifconfig
```
3. At the top of */etc/watchdog.conf*
```
sudo vi /etc/watchdog.conf
```
add the following
```
# network interface
interface = wlan0
# timeout [sec] until reboot
retry-timeout = 65
# an internet address to test
ping = 8.8.8.8
# interval [sec] of testing the connectivity
interval = 15
```

## Set hotplug to prevent hanging on boot
Update /boot/config.txt to add
```
hdmi_force_hotplug=1
```

## (Optional) Prep external drive for dogbot (more reliable than sdcard)
Create partition using fdisk (change /dev/sda to drive found using lsblk)
```
sudo fdisk /dev/sda
```

Make ext4 file system on drive and label
```
sudo mkfs -t ext4 -L DATA /dev/sda
```

Add fstab entry and mount
```
LABEL=DATA	/home/pi/dogbot	ext4	defaults	0	2
```

## (Optional) Set max USB current when using external drive
Update /boot/config.txt to add
```
max_usb_current=1
```

## (Optional) Underclock Pi CPU to prevent overheating 
Update /boot/config.txt to add
```
arm_freq=900
arm_freq_min=600
```
and check after a reboot
```
pi@raspberrypi:~ $ lscpu | grep "MHz"
CPU max MHz:           900.0000
CPU min MHz:           600.0000
```
