import logging

from util import shadow_util

THING_NAME = "dogbot"

MEAL_THING_STATE_KEY = "meal"
TREAT_THING_STATE_KEY = "treat"
WATER_THING_STATE_KEY = "water"
DISPENSE_SCHEDULED_THING_STATE_VALUE = "dispense_scheduled"

log = logging.getLogger(__name__)
logging.basicConfig()
log.setLevel(logging.DEBUG)

def dispense_meal(event, context): 
    log.info("dispense_meal")
    shadow_util.update_shadow_desired(THING_NAME, MEAL_THING_STATE_KEY, DISPENSE_THING_STATE_VALUE)

def dispense_treat(event, context): 
    log.info("dispense_treat")
    shadow_util.update_shadow_desired(THING_NAME, TREAT_THING_STATE_KEY, DISPENSE_THING_STATE_VALUE)

def dispense_water(event, context): 
    log.info("dispense_water")
    shadow_util.update_shadow_desired(THING_NAME, WATER_THING_STATE_KEY, DISPENSE_THING_STATE_VALUE)
