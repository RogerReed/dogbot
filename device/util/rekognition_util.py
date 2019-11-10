import time
import logging
import boto3

DEFAULT_REKOGNITION_MIN_CONFIDENCE = 75
DEFAULT_REKOGNITION_MAX_LABELS = 25

AWS_REGION = "us-east-1"
AWS_ACCESS_KEY_ID_FILE = "creds/aws_access_key_id.txt"
AWS_SECRET_ACCESS_KEY_FILE = "creds/aws_secret_access_key.txt"

aws_access_key_id = open(AWS_ACCESS_KEY_ID_FILE, "r").read()
aws_secret_access_key = open(AWS_SECRET_ACCESS_KEY_FILE, "r").read()


def rekognize_label_in_image(filename, label_name, max_labels=DEFAULT_REKOGNITION_MAX_LABELS, min_confidence=DEFAULT_REKOGNITION_MIN_CONFIDENCE):
    rekognition_client = boto3.client("rekognition",
                                      aws_access_key_id=aws_access_key_id,
                                      aws_secret_access_key=aws_secret_access_key,
                                      region_name=AWS_REGION)

    with open(filename, "rb") as image_file:
        image_bytes = image_file.read()
        rekognition_response = rekognition_client.detect_labels(
            Image={
                'Bytes': image_bytes
            },
            MaxLabels=max_labels,
            MinConfidence=min_confidence
        )

        logging.debug("rekognition response: %s", rekognition_response)

        label_dict = next((label for label in rekognition_response['Labels'] if label['Name'].lower(
        ) == label_name.lower()), None)
        label_rekognized = label_dict is not None and label_dict["Confidence"] > min_confidence

        logging.info("%s%s rekognized in photo" %
                     (label_name, ("" if label_rekognized else " not")))

        return label_rekognized
