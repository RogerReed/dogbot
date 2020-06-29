import time
import logging

from io import BytesIO
from picamera import PiCamera

CAMERA_WARMUP_SEC = 2
CAMERA_ROTATION_DEG = 180 # rotating based on physical placement in cabinet
CAMERA_X_RES_PX = 1024 # max 2592 
CAMERA_Y_RES_PX = 768 # max 1944
    
def init_camera():
    camera = None
    try:
        camera = PiCamera()
        camera.rotation = CAMERA_ROTATION_DEG
        camera.resolution = (CAMERA_X_RES_PX, CAMERA_Y_RES_PX)
        camera.start_preview()
        # time.sleep(CAMERA_WARMUP_SEC) # skipping warm up as not used immediately
        logging.info("camera initialized")
    except Exception as e:
        logging.error("unable to initialize camera: %s" % e)

    return camera
 
def camera_capture(camera, filename):
    camera.capture(filename)
    logging.info("camera photo captured")
