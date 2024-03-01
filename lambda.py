import json
import os
import base64
import aws_encryption_sdk
from aws_encryption_sdk import CommitmentPolicy
import boto3
from botocore.exceptions import ClientError, WaiterError
import logging as logger
 
class SesMailSender:
    """Encapsulates functions to send emails with Amazon SES."""
 
    def __init__(self, ses_client):
        """
        :param ses_client: A Boto3 Amazon SES client.
        """
        self.ses_client = ses_client
 
 
    def send_email(self, source, destination, subject, text, reply_tos=None):
        """
        Sends an email.
 
        Note: If your account is in the Amazon SES  sandbox, the source and
        destination email accounts must both be verified.
 
        :param source: The source email account.
        :param destination: The destination email account.
        :param subject: The subject of the email.
        :param text: The plain text version of the body of the email.
        :param html: The HTML version of the body of the email.
        :param reply_tos: Email accounts that will receive a reply if the recipient
                          replies to the message.
        :return: The ID of the message, assigned by Amazon SES.
        """
        send_args = {
            "Source": source,
            "Destination": {
                "ToAddresses":[destination],
            },
            "Message": {
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": text}},
            },
        }
        if reply_tos is not None:
            send_args["ReplyToAddresses"] = reply_tos
        try:
            response = self.ses_client.send_email(**send_args)
            message_id = response["MessageId"]
            logger.info(
                "Sent mail %s from %s to %s.", message_id, source, destination
            )
        except ClientError:
            logger.exception(
                "Couldn't send mail from %s to %s.", source, destination
            )
            raise
        else:
            return message_id
        
 
 
client = aws_encryption_sdk.EncryptionSDKClient(commitment_policy=CommitmentPolicy.REQUIRE_ENCRYPT_ALLOW_DECRYPT)
key_arn = os.environ['KEY_ID']
kms_kwargs = dict(key_ids=[key_arn])
master_key_provider = aws_encryption_sdk.StrictAwsKmsMasterKeyProvider(**kms_kwargs)
 
ses_client = boto3.client("ses")
ses_mail_sender = SesMailSender(ses_client)
 
def lambda_handler(event, context):
    print(json.dumps(event)) # Print full event received by Cognito
    b64_decoded = base64.b64decode(event['request']['code'])
    plaintext, decrypted_header = client.decrypt(source=b64_decoded, key_provider=master_key_provider)
 
    destination = event['request']['userAttributes']['email']
    domain = destination.split("@")
 
 # If the User's domain is amazon.com the expeditor (Sender) is from gmail.com and vice versa..
 # Tested with Sign up but it can be any of the events described here => https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-custom-email-sender.html#trigger-source 
    if domain[1] == "amazon.com":
        source = "expeditor@gmail.com"
        test_message_text = f"Your Code is {plaintext.decode()}"
 
        print(f"Sending mail from {source} to {destination}.")
        ses_mail_sender.send_email(
            source,
            destination,
            "Hello from the Amazon SES mail demo!",
            test_message_text
        )
    elif domain[1] == "gmail.com":
        source = "expeditor@amazon.com"
        test_message_text = f"Your Code is {plaintext.decode()}"
 
        print(f"Sending mail from {source} to {destination}.")
        ses_mail_sender.send_email(
            source,
            destination,
            "Hello from the Amazon SES mail demo!",
            test_message_text
        )
 
    return event
