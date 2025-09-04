import argparse
import logging
from minio import Minio

parser = argparse.ArgumentParser(
    prog="pull.py",
    description="""Minio uploader.
    Usage: python pull.py <file to pull> <bucket> <save filepath>"""
)

parser.add_argument('filename', help='File to pull')
parser.add_argument('bucket', help='Bucket to pull from')
parser.add_argument('file_save', help='File to save to')

args = parser.parse_args()
filename = args.filename
bucket = args.bucket

file_save = args.file_save

client = Minio(
    "minio-console.mcfe.itservices.manchester.ac.uk",
    access_key="oJoz9gvQ4d1GJPmrl9YN",
    secret_key="cZ7psKhLQ5P3V5OkUXGV5nNItojEZgZLaUHyXoMH",
    secure=True
)

buckets = client.list_buckets()
if bucket not in buckets:
    logging.error("Error: Bucket %s does not exist.", bucket)
else:
    print(f'Pulling {filename} from {bucket} to {file_save}')
    client.fget_object(bucket, filename, file_save)
