# mock for working locally (i.e. not on a raspberry pi)

LED_COUNT = 150 

class Adafruit_NeoPixel(object):
    def __init__(self, num, pin, freq_hz=800000, dma=10, invert=False,
			brightness=255, channel=0, strip_type=0):
        pass

    def begin(self):
        pass
        
    def show(self):
        pass

    def numPixels(self):
        return LED_COUNT

    def setPixelColor(self, i, color):
        pass