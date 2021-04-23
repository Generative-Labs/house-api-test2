import os

S3_BUCKET = os.environ['S3_BUCKET']
AWS_KEY = os.environ['AWS_KEY']
AWS_SECRET = os.environ["AWS_SECRET_ACCESS_KEY"]
S3_LOCATION = 'http://{}.s3.amazonaws.com'.format(S3_BUCKET)
CLOUDFRONT = 'https://d97ch61yqe5j6.cloudfront.net'
# AVATAR = S3_LOCATION+'avatar'

SECRET_KEY = os.urandom(32)
DEBUG = True
PORT = 5000
