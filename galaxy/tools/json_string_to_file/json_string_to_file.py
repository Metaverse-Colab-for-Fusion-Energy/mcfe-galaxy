import json
import argparse

# Read in command line arguments
parser = argparse.ArgumentParser()

parser.add_argument('json_string')
parser.add_argument('file')

args = parser.parse_args()

string_array = []
with open(args.json_string, 'r') as f:
    for line in f:
        string_array.append(line)
    json_string = ' '.join(string_array)

print(json_string)

# Check if the json string is valid & convert to py dict
try:
    data = json.loads(json_string)
except Exception as e:
    print(e)
    try:
        data = json_string.replace("'", '"')
        data = data.replace("True", "true").replace("False", "false")
        data = json.loads(data)
    except Exception as e:
        print(e)
        try:
            data = json_string.replace("'", '"')
            data = data.replace("True", "true").replace("False", "false")
            data = data[1:-1]
            data = json.loads(data)
        except Exception as e:
            print(e)
            raise ValueError('The json string is not valid')

# Write the dictionary to a file
with open(args.file, 'w') as f:
    json.dump(data, f)
