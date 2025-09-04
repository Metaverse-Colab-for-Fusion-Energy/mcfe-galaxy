import requests
import json
import argparse
import mimetypes
import os

parser = argparse.ArgumentParser(
    prog="upload_nucleus.py",
    description="""nucleus upload.
    Usage: python upload_nucleus.py <url> <username> <password> <file>"""
)

parser.add_argument('url', help='url')
parser.add_argument('username', help='username')
parser.add_argument('password', help='password')
parser.add_argument('filepath', help='file path')
parser.add_argument('file_name', help='File Name')
parser.add_argument('file_type', help='File Type')

args = parser.parse_args()

url = args.url
username = args.username
password = args.password
filepath = args.filepath
file_name = args.file_name
file_type = args.file_type

new_filepath = f"{file_name}.{file_type}"
print(new_filepath)

os.symlink(filepath, new_filepath)


# ------------------------------------------------------------------------------
# Authenticate with Authelia

AUTHELIA = "auth.mcfe.itservices.manchester.ac.uk"
# TODO: Change to bind user or have as tool input
AUTHELIA_USERNAME = 'authelia_galaxy_bind'
AUTHELIA_PASSWORD = 'r4l/@p8f42mu57M@'
NUCLEUS_BASE = "nucleus-api.mcfe.itservices.manchester.ac.uk"

response = requests.post(
    f"https://{AUTHELIA}/api/firstfactor",
    headers={"accept": "application/json", "Content-Type": "application/json"},
    data=json.dumps({"username": AUTHELIA_USERNAME,
                     "password": AUTHELIA_PASSWORD}),
)

cookies = response.cookies

print("Authelia response:", response.json())

# ------------------------------------------------------------------------------
# Get user info (validate Authelia session)

response = requests.get(
    f"https://{AUTHELIA}/api/user/info",
    headers={"accept": "application/json"},
    cookies=cookies,
)

print("User info:", response.json())

# Upload projects

# Get file type
file_type, _ = mimetypes.guess_type(new_filepath)

print(f"File type: {file_type}")

# Open the file and read its content
with open(new_filepath, "rb") as file_read:
    file_content = file_read.read()

# Construct the files dictionary with the file content
files = {"file": (new_filepath, file_content, f"{file_type}")}

response = requests.post(
    f"https://{NUCLEUS_BASE}/omnicli/upload?url={url}",
    headers={
        "accept": "application/json",
        "username": username,
        "password": password,
    },
    files=files,
    cookies=cookies,
)

try:
    output = response.json()
    print(json.dumps(output, indent=4))
except json.JSONDecodeError:
    print("Projects:", response.text)
