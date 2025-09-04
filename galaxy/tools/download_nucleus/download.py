import requests
import json
import argparse

parser = argparse.ArgumentParser(
    prog="download_nucleus.py",
    description="""nucleus download.
    Usage: python download.py <url> <username> <password> <file>"""
)

parser.add_argument('url', help='url')
parser.add_argument('username', help='username')
parser.add_argument('password', help='password')
parser.add_argument('file', help='file')

args = parser.parse_args()
url = args.url
username = args.username
password = args.password
files = args.file


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

while True:
    file_name = url.split("/")[-1]
    if "." not in file_name:
        print("Not a valid URL for downloading single files.")
        print("Please input another valid URL")
    else:
        break

response = requests.get(
    f"https://{NUCLEUS_BASE}/omnicli/download?url={url}",
    headers={
        "accept": "application/json",
        "username": username,
        "password": password
    },
    cookies=cookies,
)

# user_profile = os.path.expanduser("~")
# destination_path = os.path.join(user_profile, file_name)

# Write the response content to the output file
with open(files, "wb") as file:
    file.write(response.content)
