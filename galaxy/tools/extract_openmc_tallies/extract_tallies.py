import openmc
import json
import argparse

parser = argparse.ArgumentParser(
    prog='openmc_parametric.py',
    description='''OpenMC parametric CAD run script.
    Useage: python openmc_parametric.py <statepoint_f> <output_f>'''
)

parser.add_argument(
    'statepoint_file',
    help='statepoint.5.h5 file with the results of the simulation. Format: h5'
)
parser.add_argument(
    'output_file',
    help='File to write the results to. Format: JSON'
)
args = parser.parse_args()

statepoint_filename = args.statepoint_file
output_filename = args.output_file

sp = openmc.StatePoint(statepoint_filename)
tally_dict = sp.tallies

tally_names = []

for tally in tally_dict:
    tally_names.append(tally_dict[tally].name)

tallies = {}

for name in tally_names:
    tally = sp.get_tally(name=name)
    tally_dict = json.loads(tally.get_pandas_dataframe().to_json())
    tallies[name] = tally_dict

with open(output_filename, 'w') as write_f:
    json.dump(tallies, write_f)
