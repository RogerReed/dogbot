import time
import logging

from slackclient import SlackClient
 
SLACK_API_TOKEN_FILE = "creds/slack_api_token.txt"
DEFAULT_SLACK_CHANNEL = "#general"

slack_api_token=open(SLACK_API_TOKEN_FILE, "r").read()

def post_image_to_slack(filename, slack_image_title, slack_channel=DEFAULT_SLACK_CHANNEL):
    with open(filename, "rb") as image_file:
        image_bytes = image_file.read()
        slack_token = open(SLACK_API_TOKEN_FILE, "r").read()
        sc = SlackClient(slack_api_token)
        slack_response_dict = sc.api_call('files.upload', channels=slack_channel, title=slack_image_title, file=image_bytes)
        logging.debug("slack response: %s", slack_response_dict)
        if slack_response_dict['ok']:
                logging.info("photo posted to slack")
        else:
                logging.error("problem posting photo to slack")
