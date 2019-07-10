import time
import logging

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
 
ROOT_CA = "certs/AmazonRootCA1.pem"
PRIVATE_KEY = "certs/private.pem.key"
CERT_FILE = "certs/certificate.pem.crt"

SHADOW_CLIENT_NAME = "shadow-client"

def init_shadow_handler(ats_iot_host, ats_iot_port, shadow_name):
    shadow_handler = None
    
    try:
        shadow_client = AWSIoTMQTTShadowClient(SHADOW_CLIENT_NAME)
        shadow_client.configureEndpoint(ats_iot_host, ats_iot_port)
        shadow_client.configureCredentials(ROOT_CA, PRIVATE_KEY,
                                        CERT_FILE)
        shadow_client.configureConnectDisconnectTimeout(10)
        shadow_client.configureMQTTOperationTimeout(5)
        shadow_client.connect()

        shadow_handler = shadow_client.createShadowHandlerWithName(
            shadow_name, True)

        logging.info('AWS IoT shadow handler initialized')
    except Exception as e:
        logging.error("unable to initialize shadow handler: %s" % e)

    return shadow_handler 