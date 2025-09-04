import json
import argparse

# Read in command line arguments
parser = argparse.ArgumentParser()

parser.add_argument('key')
parser.add_argument('value')
parser.add_argument('json_output')

args = parser.parse_args()

# Read in data from the value file
with open(args.value, 'r') as f:
    value = f.read()

# Create Dict
data = {args.key: value}

# Write the dictionary to a file
with open(args.json_output, 'w') as f:
    json.dump(data, f)
