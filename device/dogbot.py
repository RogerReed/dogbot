import RPi.GPIO as GPIO
import json
import time
import logging
import logging.config
import uuid
import thread
import os
import signal
import sys
 
from threading import Lock, Thread, Event
from util.neopixel_util import Color
from util import neopixel_util, camera_util, rekognition_util, shadow_util, slack_util

logging.config.fileConfig('logging.ini')

DOG_NAME = "Lula"
SHADOW_NAME = "dogbot" 

ATS_IOT_ENDPOINT_HOST = "a19u360l2irzg8-ats.iot.us-east-1.amazonaws.com"
ATS_IOT_ENDPOINT_PORT = 8883

class Dogbot:
    DOGBOT_ON_THING_STATE_KEY = "dogbot_on"
    MEAL_THING_STATE_KEY = "meal"
    PAUSE_MEAL_THING_STATE_KEY = "pause_meal"
    TREAT_THING_STATE_KEY = "treat"
    WATER_THING_STATE_KEY = "water"
    READY_THING_STATE_VALUE = "ready"
    DISPENSE_THING_STATE_VALUE = "dispense"
    DISPENSE_SCHEDULED_THING_STATE_VALUE = "dispense_scheduled"

    MEAL_SLACK_IMAGE_MESSAGE = "{dog_name} time to eat!"
    TREAT_SLACK_IMAGE_MESSAGE = "{dog_name} here is a treat!"
    WATER_SLACK_IMAGE_MESSAGE = "{dog_name} more water!"

    MEAL_AUGER_MOTOR_PIN = 13
    TREAT_AUGER_MOTOR_PIN = 19
    WATER_RELAY_PIN = 26
 
    # slight duration changes in run time determine how many treats, or amount of food
    # and water dispenses - ideally a motor with lower rotation per minute (rpm) would
    # be used, but these faster motors were what I had on hand, or pwm could be used
    # to control motor speed
    TREAT_AUGER_MOTOR_RUN_SEC = 5
    MEAL_AUGER_MOTOR_RUN_SEC = 8
    REFILL_WATER_RELAY_ON_SEC = 20
  
    DOGBOT_STATE_IDLE = 0
    DOGBOT_STATE_FEEDING = 1
    DOGBOT_STATE_TREATING = 2
    DOGBOT_STATE_WATERING = 3
    DOGBOT_STATE_CHANGING_PAUSE_MEAL = 4
 
    REKOGNITION_LABEL_MATCH = "dog"

    FIRST_CAMERA_CAPTURE_DELAY_SEC = 0
    SECOND_CAMERA_CAPTURE_DELAY_SEC = 15
    THIRD_CAMERA_CAPTURE_DELAY_SEC = 30

    SHADOW_OPERATION_TIMEOUT_SEC = 30

    def __init__(self, dog_name, shadow_name, ats_endpoint_host, ats_endpoint_port):
        self.dog_name = dog_name
        self.shadow_name = shadow_name

        self.meal_slack_image_message = Dogbot.MEAL_SLACK_IMAGE_MESSAGE.format(
            dog_name=self.dog_name)
        self.treat_slack_image_message = Dogbot.TREAT_SLACK_IMAGE_MESSAGE.format(
            dog_name=self.dog_name)
        self.water_slack_image_message = Dogbot.WATER_SLACK_IMAGE_MESSAGE.format(
            dog_name=self.dog_name)

        self.dogbot_state = Dogbot.DOGBOT_STATE_IDLE
        self.dogbot_state_lock = Lock()
        self.dogbot_state_active_interrupt = Event()
        # used to only upload one image at time to avoid overloading slow network
        self.image_transfer_lock = Lock() 

        self.initial_shadow_get = True
        self.pause_meal_enabled = False
 
        self.idle_color_index = 1

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(Dogbot.MEAL_AUGER_MOTOR_PIN, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(Dogbot.TREAT_AUGER_MOTOR_PIN, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(Dogbot.WATER_RELAY_PIN, GPIO.OUT, initial=GPIO.HIGH)

        self.shadow_handler = None
        while self.shadow_handler == None:
            try:
                self.shadow_handler = shadow_util.init_shadow_handler(
                    ats_endpoint_host, ats_endpoint_port, shadow_name)
            except Exception as e:
                logging.error("unable to initialize shadow handler; retrying in 5 sec: %s" % e)    
                time.sleep(5)
 
        self.camera = camera_util.init_camera()
 
        self.strip = neopixel_util.init_strip()

    def start(self):
        # if any pending requests for meal, treat, or water while offline ignore
        self.update_shadow_reported(Dogbot.DOGBOT_ON_THING_STATE_KEY,
                                    True)
        self.update_shadow_reported(Dogbot.MEAL_THING_STATE_KEY,
                                    Dogbot.READY_THING_STATE_VALUE)
        self.update_shadow_reported(Dogbot.TREAT_THING_STATE_KEY,
                                    Dogbot.READY_THING_STATE_VALUE)
        self.update_shadow_reported(Dogbot.WATER_THING_STATE_KEY,
                                    Dogbot.READY_THING_STATE_VALUE)

        while True:
            self.acquire_dogbot_state_lock()

            if self.dogbot_state == Dogbot.DOGBOT_STATE_IDLE:
                self.check_shadow()
            else:
                time.sleep(0.5)
                continue

            self.release_dogbot_state_lock()

            # each idle_color_pixel takes about 4 seconds, so running multiple times
            # to reduce the frequency of check shadow (MQTT) calls
            self.idle_color_pixel() 
            self.idle_color_pixel()
  
    def acquire_dogbot_state_lock(self):
        self.dogbot_state_lock.acquire()

    def release_dogbot_state_lock(self):
        self.dogbot_state_lock.release()
 
    def acquire_image_transfer_lock(self):
        self.image_transfer_lock.acquire()

    def release_image_transfer_lock(self):
        self.image_transfer_lock.release()

    def set_dogbot_state(self, state):
        self.dogbot_state = state
        if self.dogbot_state == Dogbot.DOGBOT_STATE_IDLE:
            self.dogbot_state_active_interrupt.clear()
        else:
            self.dogbot_state_active_interrupt.set()

    def send_rekognized_dog_to_slack(self, slack_image_title, delay_sec=0):
        image_filename = "/tmp/%s.jpg" % str(uuid.uuid4())

        try:
            time.sleep(delay_sec)
            camera_util.camera_capture(self.camera, image_filename)
        except Exception as e:
            logging.error("unable to camera capture: %s" % e)
            return
  
        self.acquire_image_transfer_lock()
        try:
            if rekognition_util.rekognize_label_in_image(image_filename, Dogbot.REKOGNITION_LABEL_MATCH):
                slack_util.post_image_to_slack(image_filename, slack_image_title)
        except Exception as e:
            logging.error("unable to send rekognized dog to slack: %s" % e)
        finally:
            self.release_image_transfer_lock()
            os.remove(image_filename)

    def shadow_get_callback(self, payload, response_status, token):
        logging.info("shadow check (%s)" % response_status)

        logging.debug('GET: $aws/things/' + self.shadow_name +
                      '/shadow/get/#')
        logging.debug("payload = " + payload)
        logging.debug("responseStatus = " + response_status)
        logging.debug("token = " + token)
 
        payload_dict = json.loads(payload)
        logging.debug("shadow_get_callback payload_dict: %s" % payload_dict)
        if 'state' in payload_dict.keys():
            if self.initial_shadow_get:
                if 'desired' in payload_dict['state'].keys():
                    desired_dict = payload_dict['state']['desired']

                    if Dogbot.PAUSE_MEAL_THING_STATE_KEY in desired_dict.keys() and desired_dict[Dogbot.PAUSE_MEAL_THING_STATE_KEY]:
                        self.pause_meal_enabled = True

                self.initial_shadow_get = False

            if 'delta' in payload_dict['state'].keys():
                delta_dict = payload_dict['state']['delta']
                logging.debug('shadow delta: %s' % delta_dict)

                if Dogbot.MEAL_THING_STATE_KEY in delta_dict.keys():
                    self.handle_shadow_meal_delta(
                        delta_dict[Dogbot.MEAL_THING_STATE_KEY])

                if Dogbot.TREAT_THING_STATE_KEY in delta_dict.keys():
                    self.handle_shadow_treat_delta(
                        delta_dict[Dogbot.TREAT_THING_STATE_KEY])

                if Dogbot.WATER_THING_STATE_KEY in delta_dict.keys():
                    self.handle_shadow_water_delta(
                        delta_dict[Dogbot.WATER_THING_STATE_KEY])

                if Dogbot.PAUSE_MEAL_THING_STATE_KEY in delta_dict.keys():
                    self.handle_shadow_pause_meal_delta(
                        delta_dict[Dogbot.PAUSE_MEAL_THING_STATE_KEY])

            elif 'desired' in payload_dict['state'].keys():
                # if request for pause or unpause scheduled feeding and already the same value
                # delta will not be present, so handle desired and show neopixel change again
                desired_dict = payload_dict['state']['desired']
                logging.debug('shadow desired: %s' % desired_dict)

                if Dogbot.PAUSE_MEAL_THING_STATE_KEY in desired_dict.keys():
                    self.handle_shadow_pause_meal_delta(
                        desired_dict[Dogbot.PAUSE_MEAL_THING_STATE_KEY])

    def shadow_update_callback(self, payload, response_status, token):
        logging.debug('UPDATE: $aws/things/' + self.shadow_name +
                      '/shadow/update/#')
        logging.debug("payload = " + payload)
        logging.debug("responseStatus = " + response_status)
        logging.debug("token = " + token)

    def shadow_delete_callback(self, payload, response_status, token):
        logging.debug('DELETE: $aws/things/' + self.shadow_name +
                      '/shadow/delete/#')
        logging.debug("payload = " + payload)
        logging.debug("responseStatus = " + response_status)
        logging.debug("token = " + token)

    def delete_shadow(self):
        try:
            self.shadow_handler.shadowDelete(
                self.shadow_delete_callback, self.SHADOW_OPERATION_TIMEOUT_SEC)
        except Exception as e:
            logging.error("unable to delete shadow: %s" % e)

    def update_shadow_reported(self, key, value):
        try:
            payload_dict = {
                "state": {
                    "desired": {key: None},
                    "reported": {key: value}
                }
            }
            self.shadow_handler.shadowUpdate(
                json.dumps(payload_dict),
                self.shadow_update_callback, self.SHADOW_OPERATION_TIMEOUT_SEC)
        except Exception as e:
            logging.error("unable to update shadow: %s" % e)                

    def check_shadow(self):
        try:
            self.shadow_handler.shadowGet(
                self.shadow_get_callback, self.SHADOW_OPERATION_TIMEOUT_SEC)
        except Exception as e:
            logging.error("unable to check shadow: %s" % e)
 
    def handle_shadow_pause_meal_delta(self, shadow_pause_meal_delta):
        logging.debug('handle_shadow_pause_meal_delta: %s' % shadow_pause_meal_delta)
        if shadow_pause_meal_delta:
            self.pause_meal()
        else:
            self.unpause_meal()

    def handle_shadow_meal_delta(self, shadow_meal_delta):
        logging.debug('handle_shadow_meal_delta: %s' % shadow_meal_delta)
        if shadow_meal_delta == Dogbot.DISPENSE_THING_STATE_VALUE:
            self.dispense_meal()
        # if dispense scheduled event, check if scheduled feeding disabled
        elif shadow_meal_delta == Dogbot.DISPENSE_SCHEDULED_THING_STATE_VALUE and not self.pause_meal_enabled:
            self.dispense_meal()
        else:
            self.update_shadow_reported(Dogbot.MEAL_THING_STATE_KEY,
                                        Dogbot.READY_THING_STATE_VALUE)

    def handle_shadow_treat_delta(self, shadow_treat_delta):
        logging.debug('handle_shadow_treat_delta: %s' % shadow_treat_delta)
        if shadow_treat_delta == Dogbot.DISPENSE_THING_STATE_VALUE:
            self.dispense_treat()
        # if dispense scheduled event, check if scheduled feeding disabled
        elif shadow_treat_delta == Dogbot.DISPENSE_SCHEDULED_THING_STATE_VALUE and not self.pause_meal_enabled:
            self.dispense_treat()
        else:
            self.update_shadow_reported(Dogbot.TREAT_THING_STATE_KEY,
                                        Dogbot.READY_THING_STATE_VALUE)            

    def handle_shadow_water_delta(self, shadow_water_delta):
        logging.debug('handle_shadow_water_delta: %s' % shadow_water_delta)
        # always dispense water to keep bowl fresh, even if paused
        if shadow_water_delta == Dogbot.DISPENSE_THING_STATE_VALUE or shadow_water_delta == Dogbot.DISPENSE_SCHEDULED_THING_STATE_VALUE:
            self.dispense_water()

    def pause_meal(self):
        self.acquire_dogbot_state_lock()
        logging.info('scheduled meals paused')
        self.set_dogbot_state(Dogbot.DOGBOT_STATE_CHANGING_PAUSE_MEAL)

        self.update_shadow_reported(Dogbot.PAUSE_MEAL_THING_STATE_KEY, True)
        neopixel_util.colorWipe(self.strip, Color(0, 255, 0), 5)
        neopixel_util.colorWipe(self.strip, neopixel_util.COLOR_BLACK, 5)
        self.pause_meal_enabled = True

        self.set_dogbot_state(Dogbot.DOGBOT_STATE_IDLE)
        self.release_dogbot_state_lock()

    def unpause_meal(self):
        self.acquire_dogbot_state_lock()
        logging.info('resuming scheduled meals')
        self.set_dogbot_state(Dogbot.DOGBOT_STATE_CHANGING_PAUSE_MEAL)

        self.update_shadow_reported(Dogbot.PAUSE_MEAL_THING_STATE_KEY, False)
        neopixel_util.colorWipe(self.strip, Color(255, 0, 0), 5)
        neopixel_util.colorWipe(self.strip, neopixel_util.COLOR_BLACK, 5)
        self.pause_meal_enabled = False
 
        self.set_dogbot_state(Dogbot.DOGBOT_STATE_IDLE)
        self.release_dogbot_state_lock()

    def dispense_meal(self):
        self.acquire_dogbot_state_lock()
        logging.info('dispensing meal')
        self.set_dogbot_state(Dogbot.DOGBOT_STATE_FEEDING)

        self.update_shadow_reported(Dogbot.MEAL_THING_STATE_KEY,
                                    Dogbot.DISPENSE_THING_STATE_VALUE)
        thread.start_new_thread(neopixel_util.rainbow, (self.strip, 10))

        GPIO.output(Dogbot.MEAL_AUGER_MOTOR_PIN, GPIO.LOW)
        time.sleep(Dogbot.MEAL_AUGER_MOTOR_RUN_SEC)
        GPIO.output(Dogbot.MEAL_AUGER_MOTOR_PIN, GPIO.HIGH)

        neopixel_util.colorWipe(self.strip, neopixel_util.COLOR_BLACK, 2)
        self.update_shadow_reported(
            Dogbot.MEAL_THING_STATE_KEY, Dogbot.READY_THING_STATE_VALUE)

        self.start_send_rekognized_dog_to_slack_threads(
            self.meal_slack_image_message)

        self.set_dogbot_state(Dogbot.DOGBOT_STATE_IDLE)
        self.release_dogbot_state_lock()

    def dispense_treat(self):
        self.acquire_dogbot_state_lock()

        logging.info('dispensing treat')
        self.set_dogbot_state(Dogbot.DOGBOT_STATE_TREATING)

        self.update_shadow_reported(Dogbot.TREAT_THING_STATE_KEY,
                                    Dogbot.DISPENSE_THING_STATE_VALUE)
        thread.start_new_thread(
            neopixel_util.theaterChaseRainbow, (self.strip,))

        GPIO.output(Dogbot.TREAT_AUGER_MOTOR_PIN, GPIO.LOW)
        time.sleep(Dogbot.TREAT_AUGER_MOTOR_RUN_SEC)
        GPIO.output(Dogbot.TREAT_AUGER_MOTOR_PIN, GPIO.HIGH)
 
        neopixel_util.colorWipe(self.strip, neopixel_util.COLOR_BLACK, 2)
        self.update_shadow_reported(
            Dogbot.TREAT_THING_STATE_KEY, Dogbot.READY_THING_STATE_VALUE)

        self.start_send_rekognized_dog_to_slack_threads(
            self.treat_slack_image_message)

        self.set_dogbot_state(Dogbot.DOGBOT_STATE_IDLE)
        self.release_dogbot_state_lock()

    def dispense_water(self):
        self.acquire_dogbot_state_lock()

        logging.info('dispensing water')
        self.set_dogbot_state(Dogbot.DOGBOT_STATE_WATERING)

        self.update_shadow_reported(Dogbot.WATER_THING_STATE_KEY,
                                    Dogbot.DISPENSE_THING_STATE_VALUE)
        thread.start_new_thread(neopixel_util.colorWipe,
                                (self.strip, Color(0, 0, 255)))

        GPIO.output(Dogbot.WATER_RELAY_PIN, GPIO.LOW)
        time.sleep(Dogbot.REFILL_WATER_RELAY_ON_SEC)
        GPIO.output(Dogbot.WATER_RELAY_PIN, GPIO.HIGH)

        neopixel_util.colorWipe(self.strip, neopixel_util.COLOR_BLACK, 2)
        self.update_shadow_reported(
            Dogbot.WATER_THING_STATE_KEY, Dogbot.READY_THING_STATE_VALUE)

        self.start_send_rekognized_dog_to_slack_threads(
            self.water_slack_image_message)

        self.set_dogbot_state(Dogbot.DOGBOT_STATE_IDLE)
        self.release_dogbot_state_lock()

    """ Rotates through various colors on a single pixel color wipe to show
        dogbot is on.  If scheduled feeding is paused the color is always red.
    """
    def idle_color_pixel(self):
        logging.debug("pause_meal_enabled: %s", self.pause_meal_enabled)
        if self.pause_meal_enabled:
            neopixel_util.colorWipeSingleRoundtrip(
                self.strip, Color(0, 255, 0), 12, self.dogbot_state_active_interrupt)
            return

        logging.debug("idle_color_index: %s", self.idle_color_index)

        if self.idle_color_index == 1:
            neopixel_util.colorWipeSingleRoundtrip(self.strip, Color(
                255, 72, 196), 12, self.dogbot_state_active_interrupt)
        elif self.idle_color_index == 2:
            neopixel_util.colorWipeSingleRoundtrip(self.strip, Color(
                43, 209, 252), 12, self.dogbot_state_active_interrupt)
        elif self.idle_color_index == 3:
            neopixel_util.colorWipeSingleRoundtrip(self.strip, Color(
                243, 234, 95), 12, self.dogbot_state_active_interrupt)
        elif self.idle_color_index == 4:
            neopixel_util.colorWipeSingleRoundtrip(self.strip, Color(
                192, 77, 249), 12, self.dogbot_state_active_interrupt)
        elif self.idle_color_index == 5:
            neopixel_util.colorWipeSingleRoundtrip(self.strip, Color(
                255, 63, 63), 12, self.dogbot_state_active_interrupt)
        elif self.idle_color_index == 6:
            neopixel_util.colorWipeSingleRoundtrip(self.strip, Color(
                63, 255, 63), 12, self.dogbot_state_active_interrupt)
            self.idle_color_index = 0

        self.idle_color_index = self.idle_color_index + 1

    def start_send_rekognized_dog_to_slack_threads(self, slack_image_message):
        thread.start_new_thread(self.send_rekognized_dog_to_slack,
                                (slack_image_message, Dogbot.FIRST_CAMERA_CAPTURE_DELAY_SEC))
        thread.start_new_thread(self.send_rekognized_dog_to_slack,
                                (slack_image_message, Dogbot.SECOND_CAMERA_CAPTURE_DELAY_SEC))
        thread.start_new_thread(self.send_rekognized_dog_to_slack,
                                (slack_image_message, Dogbot.THIRD_CAMERA_CAPTURE_DELAY_SEC))

    def sigterm_handler(self, signal, frame):
        self.update_shadow_reported(Dogbot.DOGBOT_ON_THING_STATE_KEY,
                                    False)
        sys.exit(0)

def main():
    dogbot = Dogbot(DOG_NAME, SHADOW_NAME, ATS_IOT_ENDPOINT_HOST,
           ATS_IOT_ENDPOINT_PORT)
    signal.signal(signal.SIGTERM, dogbot.sigterm_handler) 
    dogbot.start()

if __name__ == "__main__":
    main()
