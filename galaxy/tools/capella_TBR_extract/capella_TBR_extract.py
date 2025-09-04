import json
import argparse

# Import all command line arguments
# Example python3 '$__tool_directory__/json_dict_return.py' --tallies '$tallies_json' --TBR '$TBR_mean' --TBR_std '$TBR_std'
parser = argparse.ArgumentParser(description='Extract TBR from Capella output JSON')

parser.add_argument('--tallies', type=str, help='JSON file containing tallies')
parser.add_argument('--TBR', type=str, help='Mean TBR value')
parser.add_argument('--TBR_std', type=str, help='Standard deviation of TBR value')

args = parser.parse_args()

# Read in the JSON file
with open(args.tallies, 'r') as read_f:
    tallies = json.load(read_f)

# Read all the TBR values from the JSON file
TBRs = []
for key, value in tallies.items():
    if 'TBR' in key:
        TBRs.append(value)

TBR = 0
TBR_STD = 0

for item in TBRs:
    TBR += item['mean']['0']
    TBR_STD += item['std. dev.']['0']

# Write the values to the passed variables
with open(args.TBR, 'w') as write_f:
    write_f.write(str(TBR))

with open(args.TBR_std, 'w') as write_f:
    write_f.write(str(TBR_STD))
