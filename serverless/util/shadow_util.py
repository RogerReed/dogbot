import boto3
import json 
import logging 

AWS_REGION_NAME = "us-east-1"

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

def update_shadow_desired(thing_name, key, value):
    iot_payload_dict = {
        "state": {
            "desired" : {key:value}
        }
    }
    shadow_client = boto3.client("iot-data", AWS_REGION_NAME)
    update_thing_response = shadow_client.update_thing_shadow(thingName=thing_name,
                                                    payload=json.dumps(iot_payload_dict))
    log.debug("update_thing_response: %s" % update_thing_response)

