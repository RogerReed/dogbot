# Building a Pet Monitoring Solution with AWS IoT and Alexa
Check out the associated blog with this source repo for more detail on the build.
http://alexa-dogbot.blogspot.com/

## Raspberry Pi Setup
Follow this tutorial to prep the OS, disable audio, and install the neopixel library to use PIN18 for signals as described:
https://tutorials-raspberrypi.com/connect-control-raspberry-pi-ws2812-rgb-led-strips/

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

## Deploy
1. SFTP files from this repo's *device* path to your Pi in */home/pi/dogbot* path
2. From */home/pi/dogbot* path install requirements 
```
pip install -r requirements.txt
```
3. Ensure *device/certs* are included as referenced in code

### Keep files current post deployment
Use the Visual Studio Code SFTP plugin (see .vscode/sftp.json configuration) to sync code to Raspberry Pi as you make changes.

## Install dogbot as Raspberry Pi Service Install
Copy dogbot.service to */lib/systemd/system/dogbot.service*
```
sudo systemctl daemon-reload
sudo systemctl enable dogbot.service
sudo systemctl start dogbot.service
```

## Install watchdog to ensure Pi reboots on network failure
1. Make sure your Pi libraries are up to date
2. Determine network interface you want to watch
```
ifconfig
```
3. Add the following at the top of */etc/watchdog.conf*
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

## (Optional) Underclock Pi CPU to prevent overheating 
Update /boot/config.txt to 
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