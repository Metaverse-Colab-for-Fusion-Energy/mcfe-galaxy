import openmc
import math
import numpy as np
import openmc_tally_unit_converter as otuc
from openmc_mesh_tally_to_vtk import write_mesh_tally_to_vtk
import argparse
import json

# EDIT -  better formatting on the help message
parser = argparse.ArgumentParser(
    prog="normalise_tallies.py",
    description="Normalise OpenMC heating-local tallies. Usage: python normalise_tallies.py <statepoint_file> <settings_file>",
)

parser.add_argument(
    "statepoint_file",
    help='OpenMC statepoint file from previous run (with heating-local tallies saves as a tally with the name "heating_on_mesh"). Format: h5',
)
parser.add_argument(
    "config_file",
    help="Config file with the run settings for the simulation. Format: JSON",
)

args = parser.parse_args()

config_path = args.config_file
statepoint_path = args.statepoint_file

# TODO: set up a specific settings file for this so that the settings can determine the fusion energy, fuel type etc
# Import the config file
with open(config_path, "r") as read_f:
    config = json.load(read_f)

tallies = config["tallies"]


###############
# POST-PROCESS
###############

# EDIT - this probably wont be the way this is run in the workflow - potentially as a separate tool for the post processing with the statepoint as an input
# loads in the statepoint file containing tallies
statepoint = openmc.StatePoint(filepath=statepoint_path)
print("read statepoint")
tally_to_convert = statepoint.get_tally(name="heating_on_mesh")

# Get mesh from settings
ll = tallies["lower_left"]
ur = tallies["upper_right"]
size = tallies["size"]

mesh = openmc.RegularMesh()
mesh.dimension = (size[0], size[1], size[2])
mesh.lower_left = (ll[0], ll[1], ll[2])
mesh.upper_right = (ur[0], ur[1], ur[2])

# write_mesh_tally_to_vtk(tally=tally_to_convert, filename='vtk_from_mesh.vtk')

# From https://github.com/fusion-energy/openmc_tally_unit_converter/blob/main/examples/processing_3d_mesh_heating_tally.py
# this finds the number of neutrons emitted per second by a 3MW fusion DT plasma
source_strength = otuc.find_source_strength(
    fusion_energy_per_second_or_per_pulse=3e6, reactants="DT"
)

# scaled from picosievert to sievert
result, error = otuc.process_tally(
    tally=tally_to_convert,
    required_units="watts / mm ** 3",
    source_strength=source_strength,  # number of neutrons per second emitted by the source
)

result_dict = {"heating-local": np.array(result)}

# EDIT - what output is more useful, a CSV or VTK with mesh locations on? - probably vtk at a guess
mesh.write_data_to_vtk("output.vtk", result_dict)
print("done")
# array = np.array(result) # For saving as csv
# np.savetxt('output.csv', array, delimiter=",")
