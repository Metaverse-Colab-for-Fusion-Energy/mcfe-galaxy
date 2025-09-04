import json
import argparse

# Import all command line arguments
parser = argparse.ArgumentParser(description='Generate JSON file for OpenMC')

parser.add_argument('--maj_rad', type=float, help='Major radius of the tokamak')
parser.add_argument('--triang', type=float, help='Triangularity of the tokamak')
parser.add_argument('--elong', type=float, help='Elongation of the tokamak')
parser.add_argument('--ion_temp', type=float, help='Central ion temperature')
parser.add_argument('--li6_en', type=float, help='Li6 enrichment')
parser.add_argument('--fw_thick', type=float, help='First wall thickness')

args = parser.parse_args()

# Read in the template JSON file
with open('template_input.json', 'r') as read_f:
    parametric_config = json.load(read_f)

# Update the values in the template JSON file
parametric_config['geometry']['major_radius'] = float(args.maj_rad)
parametric_config['geometry']['triangularity'] = float(args.triang)
parametric_config['geometry']['elongation'] = float(args.elong)
parametric_config['source']['central_ion_temp'] = float(args.ion_temp)
parametric_config['materials']['Blanket_inboard']['Lithium']['enrichment_amount'] = float(args.li6_en)
parametric_config['materials']['Blanket_outboard']['Lithium']['enrichment_amount'] = float(args.li6_en)
parametric_config['geometry']['firstwall_thickness'] = float(args.fw_thick)

# Write the updated JSON file
with open('output.json', 'w') as write_f:
    json.dump(parametric_config, write_f)
