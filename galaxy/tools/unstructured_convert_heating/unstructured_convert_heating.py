import openmc
import numpy as np
import openmc_tally_unit_converter as otuc
import argparse
import os

# EDIT -  better formatting on the help message
parser = argparse.ArgumentParser(
    prog="normalise_tallies.py",
    description="Normalise OpenMC heating-local tallies. Usage: python unstructured_convert_heating.py <statepoint_file> <output_file>",
)

parser.add_argument(
    "statepoint_file",
    help='OpenMC statepoint file from previous run (with heating-local tallies saves as a tally with the name "heating_on_mesh"). Format: h5',
)
parser.add_argument(
    "output_file",
    help="Output file name. Format: vtk",
)

args = parser.parse_args()

statepoint_path = args.statepoint_file
output_path = args.output_file

###############
# POST-PROCESS
###############

# EDIT - this probably wont be the way this is run in the workflow - potentially as a separate tool for the post processing with the statepoint as an input
# loads in the statepoint file containing tallies
with openmc.StatePoint(statepoint_path) as sp:
    tally = sp.tallies[1]

    umesh = sp.meshes[1]

    mesh_vols = np.array(umesh.volumes)

    thermal_flux = tally.get_values(scores=['heating-local'],
                                    filters=[openmc.EnergyFilter])

thermal_flux = thermal_flux.ravel()

source_strength = otuc.find_source_strength(
    fusion_energy_per_second_or_per_pulse=3e6, reactants="DT"
)
# print(source_strength)
result = thermal_flux * 1.60218e-19 * source_strength / mesh_vols

data_dict = {'Total Flux': result, 'Volume': mesh_vols}

# EDIT - what output is more useful, a CSV or VTK with mesh locations on? - probably vtk at a guess
umesh.write_data_to_vtk("output.vtk", data_dict, volume_normalization=False)
print("done")

os.system(f"mv output.vtk {output_path}")
