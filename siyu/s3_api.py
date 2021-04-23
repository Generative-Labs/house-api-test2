import boto3
import os
# import botocore
from siyu.awsconfig import AWS_KEY, AWS_SECRET, S3_BUCKET, S3_LOCATION, CLOUDFRONT

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_KEY,
    aws_secret_access_key=AWS_SECRET
)


def upload_file(file, path):
    """
    Function to upload a file to an S3 bucket
    path -- folder name
    """
    # print('BUCKET', S3_BUCKET)
    try:
        key = os.path.join(path, file.filename)
    except AttributeError:
        key = os.path.join(path)
    # print('key of s3', key)
    response = s3.upload_fileobj(
        file, S3_BUCKET, key)
    path = os.path.join(CLOUDFRONT, key)
    # print('s3_api', path)
    return response, path


def download_file(file_name):
    """
    Function to download a given file from an S3 bucket
    """
    # s3 = boto3.resource('s3')
    print(file_name)
    output = f"downloads/{file_name}"
    s3.download_file(S3_BUCKET, file_name, output)

    return output


def list_files():
    """
    Function to list files in a given S3 bucket
    """
    # s3 = boto3.client('s3')
    contents = []
    for item in s3.list_objects(Bucket=S3_BUCKET)['Contents']:
        contents.append(item)

    return contents
