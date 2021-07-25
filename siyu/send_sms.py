# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client
from siyu.twilioconfig import ACCOUNT_SID, AUTH_TOKEN
from collections import defaultdict
from siyu.config.twilio import SMS_URL

# Your Account Sid and Auth Token from twilio.com/console
# and set the environment variables. See http://twil.io/secure

client = Client(ACCOUNT_SID, AUTH_TOKEN)


def send_message(content, target_number, from_number='+12059315316'):
    target = target_number
    message = client.messages.create(body=content,
                                     from_=from_number,
                                     to=target
                                     )

    return(message.sid)


def available_phone():
    mobile = client.available_phone_numbers('US').local.list(limit=10)
    result = defaultdict(list)
    for number in mobile:
        result['response'].append(number.phone_number)

    return result


def provision_phone(phone_number):
    incoming_phone_number = client.incoming_phone_numbers.create(
        phone_number=phone_number,sms_method='POST',sms_url=SMS_URL)
    return incoming_phone_number.sid
