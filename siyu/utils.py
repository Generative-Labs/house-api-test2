import os
from itsdangerous import URLSafeTimedSerializer
from siyu.twilioconfig import CONFIRMATION_SECRET_KEY, CONFIRMATION_SECURITY_PASSWORD_SALT

def generate_confirmation_token(phone_number):
    serializer = URLSafeTimedSerializer(CONFIRMATION_SECRET_KEY)
    return serializer.dumps(phone_number, salt=CONFIRMATION_SECURITY_PASSWORD_SALT)


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(CONFIRMATION_SECRET_KEY)
    try:
        phone_number = serializer.loads(
            token,
            salt=CONFIRMATION_SECURITY_PASSWORD_SALT,
            max_age=expiration
        )
    except:
        return False
    return phone_number
