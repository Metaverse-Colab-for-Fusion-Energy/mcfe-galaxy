import argparse
import os
from minio import Minio

parser = argparse.ArgumentParser(
    prog="push.py",
    description="""Minio pusher.
    Usage: python push.py <file to push> <bucket>"""
)

parser.add_argument('file', help='File to push')
parser.add_argument('bucket', help='Bucket to push to')
args = parser.parse_args()

file = args.file
bucket = args.bucket

client = Minio(
    "minio-console.mcfe.itservices.manchester.ac.uk",
    access_key="oJoz9gvQ4d1GJPmrl9YN",
    secret_key="cZ7psKhLQ5P3V5OkUXGV5nNItojEZgZLaUHyXoMH",
    secure=True
)

buckets = client.list_buckets()
if bucket not in buckets:
    client.make_bucket(bucket)

head, tail = os.path.split(file)

print(f'Pushing {file} to {bucket}/{tail}')

client.fput_object(bucket, tail, file)
