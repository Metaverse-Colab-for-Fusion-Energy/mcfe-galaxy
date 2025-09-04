import json
import argparse

# Read in command line arguments
parser = argparse.ArgumentParser()

parser.add_argument('json_file_1')
parser.add_argument('json_file_2')
parser.add_argument('json_output')

args = parser.parse_args()

# Check if the json string is valid & convert to py dict
with open(args.json_file_1, 'r') as f:
    json_1 = json.load(f)

with open(args.json_file_2, 'r') as f:
    json_2 = json.load(f)

# Combine the two dictionaries
data = {**json_1, **json_2}

# Write the dictionary to a file
with open(args.json_output, 'w') as f:
    json.dump(data, f)
