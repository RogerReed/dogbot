from distutils.core import setup

setup(name             = 'RPi.GPIO',
      version          = '0.1',
      keywords         = 'Raspberry Pi GPIO Mock',
      packages         = ['RPi'])

setup(name             = 'neopixel',
      version          = '0.1',
      keywords         = 'neopixel Mock', # https://github.com/jgarff/rpi_ws281x/blob/master/python/neopixel.py
      packages         = ['neopixel'])
