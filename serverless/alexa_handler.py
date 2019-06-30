import random
import logging
import os
import boto3
import json
from util import shadow_util

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractRequestInterceptor, AbstractResponseInterceptor)
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model.ui import SimpleCard
from ask_sdk_model import Response

DOG_NAME = "Lula"

SKILL_NAME = "dogbot"

HELP_MESSAGE= "You can say feed {dog_name}, or give {dog_name} a treat, or give {dog_name} water... What can I help you with?"
HELP_REPROMPT = "What else can I help you with?"
STOP_MESSAGE = "Goodbye!"
FALLBACK_MESSAGE = "The dog bot skill can't help you with that.  It can help you take care of your dog {dog_name}.  What else can I help you with?"
FALLBACK_REPROMPT = "What can I help you with?"
EXCEPTION_MESSAGE = "Sorry. I cannot help you with that."
WELCOME_MESSAGE = "Welcome to the dog bot Skill! " #+ HELP_MESSAGE # help message too long and repetitive on startup
WHAT_DO_YOU_WANT_PROMPT = "What do you want to ask?"
FEEDING_MESSAGE = "Feeding {dog_name}!"
TREATING_MESSAGE = "Giving {dog_name} a treat!"
WATERING_MESSAGE = "Refilling {dog_name}'s water bowl!"
PAUSING_MEAL_MESSAGE = "Pausing scheduled feeding of {dog_name} until further notice."
UNPAUSING_MEAL_MESSAGE = "Resuming scheduled feeding of {dog_name}."

THING_NAME = "dogbot"

PAUSE_MEAL_THING_STATE_KEY = "pause_meal"
MEAL_THING_STATE_KEY = "meal"
TREAT_THING_STATE_KEY = "treat"
WATER_THING_STATE_KEY = "water"
DISPENSE_THING_STATE_VALUE = "dispense"

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

sb = SkillBuilder()
sb.skill_id = "amzn1.ask.skill.f0ebee3a-72fa-4e3a-8490-c4b68e7aabff"

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        handler_input.response_builder.speak(WELCOME_MESSAGE.format(dog_name=DOG_NAME)).ask(WHAT_DO_YOU_WANT_PROMPT)
        return handler_input.response_builder.response

class PauseMealIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("PauseMealIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        log.info("PauseMealIntentHandler")
        
        shadow_util.update_shadow_desired(THING_NAME, PAUSE_MEAL_THING_STATE_KEY, True)

        handler_input.response_builder.speak(PAUSING_MEAL_MESSAGE.format(dog_name=DOG_NAME)).ask(
            HELP_REPROMPT).set_card(SimpleCard(
                SKILL_NAME, HELP_MESSAGE.format(dog_name=DOG_NAME)))
        return handler_input.response_builder.response

class UnpauseMealIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("UnpauseMealIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        log.info("UnpauseMealIntentHandler")
        
        shadow_util.update_shadow_desired(THING_NAME, PAUSE_MEAL_THING_STATE_KEY, False)

        handler_input.response_builder.speak(UNPAUSING_MEAL_MESSAGE.format(dog_name=DOG_NAME)).ask(
            HELP_REPROMPT).set_card(SimpleCard(
                SKILL_NAME, HELP_MESSAGE.format(dog_name=DOG_NAME)))
        return handler_input.response_builder.response

class MealIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("MealIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        log.info("MealIntentHandler")
        
        shadow_util.update_shadow_desired(THING_NAME, MEAL_THING_STATE_KEY, DISPENSE_THING_STATE_VALUE)

        handler_input.response_builder.speak(FEEDING_MESSAGE.format(dog_name=DOG_NAME)).ask(
            HELP_REPROMPT).set_card(SimpleCard(
                SKILL_NAME, HELP_MESSAGE.format(dog_name=DOG_NAME)))
        return handler_input.response_builder.response

class TreatIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("TreatIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        log.info("TreatIntentHandler")
        
        shadow_util.update_shadow_desired(THING_NAME, TREAT_THING_STATE_KEY, DISPENSE_THING_STATE_VALUE)

        handler_input.response_builder.speak(TREATING_MESSAGE.format(dog_name=DOG_NAME)).ask(
            HELP_REPROMPT).set_card(SimpleCard(
                SKILL_NAME, HELP_MESSAGE.format(dog_name=DOG_NAME)))
        return handler_input.response_builder.response
    
class WaterIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("WaterIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        log.info("WaterIntentHandler")
        
        shadow_util.update_shadow_desired(THING_NAME, WATER_THING_STATE_KEY, DISPENSE_THING_STATE_VALUE)

        handler_input.response_builder.speak(WATERING_MESSAGE.format(dog_name=DOG_NAME)).ask(
            HELP_REPROMPT).set_card(SimpleCard(
                SKILL_NAME, HELP_MESSAGE.format(dog_name=DOG_NAME)))
        return handler_input.response_builder.response

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        log.info("HelpIntentHandler")

        handler_input.response_builder.speak(HELP_MESSAGE.format(dog_name=DOG_NAME)).ask(
            HELP_REPROMPT).set_card(SimpleCard(
                SKILL_NAME, HELP_MESSAGE.format(dog_name=DOG_NAME)))
        return handler_input.response_builder.response

class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        log.info("CancelOrStopIntentHandler")

        handler_input.response_builder.speak(STOP_MESSAGE)
        return handler_input.response_builder.response

class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        log.info("FallbackIntentHandler")

        handler_input.response_builder.speak(FALLBACK_MESSAGE.format(dog_name=DOG_NAME)).ask(
            FALLBACK_REPROMPT)
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        log.info("SessionEndedRequestHandler")

        log.info("Session ended reason: {}".format(
            handler_input.request_envelope.request.reason))
        return handler_input.response_builder.response

class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        log.info("CatchAllExceptionHandler")
        log.error(exception, exc_info=True)

        handler_input.response_builder.speak(EXCEPTION_MESSAGE).ask(
            HELP_REPROMPT)

        return handler_input.response_builder.response

class Requestlog(AbstractRequestInterceptor):
    def process(self, handler_input):
        # type: (HandlerInput) -> None
        log.debug("========Alexa Request======== {}".format(
            handler_input.request_envelope.request))

class Responselog(AbstractResponseInterceptor):
    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        log.debug("========Alexa Response======== {}".format(response))

sb.add_request_handler(LaunchRequestHandler())

sb.add_request_handler(MealIntentHandler())
sb.add_request_handler(TreatIntentHandler())
sb.add_request_handler(WaterIntentHandler())
sb.add_request_handler(PauseMealIntentHandler())
sb.add_request_handler(UnpauseMealIntentHandler())

sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

sb.add_global_request_interceptor(Requestlog())
sb.add_global_response_interceptor(Responselog())

lambda_handler = sb.lambda_handler()
