import json
import yaml
import argparse


def json_to_yaml(json_file, yaml_file):
    # Read the JSON file
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Write to a YAML file
    with open(yaml_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Convert JSON to YAML')
    parser.add_argument('json_file', type=str, help='Path to the JSON file')
    parser.add_argument('yaml_file', type=str, help='Path for the YAML file')

    args = parser.parse_args()

    json_to_yaml(args.json_file, args.yaml_file)
