# mock for working locally (i.e. not on a raspberry pi)

# Copyright (c) 2012-2014 Ben Croston

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import pkg_resources

UNKNOWN = -1

OUT = 0
IN = 1
LOW = 0
HIGH = 1
BOARD = 10
PUD_OFF = 20
PUD_DOWN = 21
PUD_UP = 22
BCM = 11

RISING = 31
FALLING = 32
BOTH = 33

SERIAL = 40
SPI = 41
I2C = 42
HARD_PWM = 43

RPI_INFO_REALISTIC = {
    'MANUFACTURER': 'Embest',
    'P1_REVISION': 3,
    'PROCESSOR': 'BCM2836',
    'RAM': '1024M',
    'REVISION': 'a21041',
    'TYPE': 'Pi2 Model B',
    'TESTING_INFO': 'This is only a Mock.'
}

RPI_INFO_MOCK = {
    'MANUFACTURER': 'Mock',
    'P1_REVISION': 0,
    'PROCESSOR': 'FAKE1234',
    'RAM': '1024M',
    'REVISION': 'z99999',
    'TYPE': 'Model Mock',
    'TESTING_INFO': 'This is only a Mock.'
}

RPI_INFO = RPI_INFO_MOCK
RPI_VERSION = 3
IS_MOCK = 1
VERSION = pkg_resources.require("RPi.GPIO")[0].version

class State(object):
    pass

def setup(*args, **xargs):
    pass

def setwarnings(*args, **kwargs):
    pass

def setmode(*args, **xargs):
    pass

def getmode(*args, **xargs):
    pass

def cleanup(*args, **xargs):
    pass

def output(*args, **xargs):
    pass

def input(*args, **kwargs):
    return ""

def set_warnings(*args, **kwargs):
    pass

def wait_for_edge(*args, **kwargs):
    pass

def add_event_detect(*args, **kwargs):
    pass

def remove_event_detect(*args, **kwargs):
    pass

def event_detected(*args, **kwargs):
    return True

def gpio_function(*args, **kwargs):
    pass

def add_event_callback(*args, **kwargs):
    pass

def PWM(*args, **kwargs):
    class PWMObject(object):
        def __init__(self, *args, **kwargs):
            pass

        def start(self, *args, **kwargs):
            pass

        def stop(self, *args, **kwargs):
            pass

        def ChangeDutyCycle(self, *args, **kwargs):
            pass

        def ChangeFrequency(self, *args, **kwargs):
            pass

    return PWMObject()