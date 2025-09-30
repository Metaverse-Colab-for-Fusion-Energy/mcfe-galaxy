import os
from omni.kit_app import KitApp
import sys
import argparse
import shutil, tempfile

parser = argparse.ArgumentParser(
    description="Upload a result file to Nucleus"
)

parser.add_argument(
    "--file",
    type=str,
    required=True,
    help="Path to the file to upload",
)

parser.add_argument(
    "--nucleus_path",
    type=str,
    required=True,
    help="Path in nucleus to upload the file to",
)

parser.add_argument(
    "--nucleus_user",
    type=str,   
    required=True,
    help="Nucleus username",
)

parser.add_argument(
    "--nucleus_pass",
    type=str,
    required=True,
    help="Nucleus password",
)

parser.add_argument(
    "--uuid",  
    type=str,
    required=False,
    help="UUID to use for naming the file in nucleus",
)

parser.add_argument(
    "--ext",  
    type=str,
    required=False,
    help="File extension",
)

args = parser.parse_args()


os.environ["OMNI_USER"] = args.nucleus_user
os.environ["OMNI_PASS"] = args.nucleus_pass

app = KitApp()
app.startup(["--enable", "omni.client"])

import omni.client
local_file = args.file
uuid_filename = args.uuid + '.' + (args.ext if args.ext else "")
nucleus_full_path = os.path.join(args.nucleus_path, uuid_filename)

result = omni.client.copy(local_file, nucleus_full_path)
if result != omni.client.Result.OK:
    print(f"Error uploading file to nucleus: {result}")
    sys.exit(1)
print(f"File uploaded to nucleus at {nucleus_full_path}")