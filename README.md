# Alexa Dogbot
http://alexa-dogbot.blogspot.com/

## Raspberry Pi Setup
Follow this tutorial to prep the OS, disable audio, and install the library to use PIN18 for neopixel signals as described:
https://tutorials-raspberrypi.com/connect-control-raspberry-pi-ws2812-rgb-led-strips/

## Development
### On the Raspberry Pi
pip install -r requirements.txt

Use the Visual Studio Code SFTP plugin (see .vscode/sftp.json configuration) to sync code to Raspberry Pi

### On your Mac
brew install pipenv
pipenv shell
sudo python setup.py install
pipenv install

## Raspberry Pi Service Install
Copy dogbot.service to /lib/systemd/system/dogbot.service
sudo systemctl daemon-reload
sudo systemctl enable dogbot.service
sudo systemctl start dogbot.service

##
/boot/config.txt
arm_freq=900
arm_freq_min=600

pi@raspberrypi:~ $ lscpu | grep "MHz"
CPU max MHz:           900.0000
CPU min MHz:           600.0000