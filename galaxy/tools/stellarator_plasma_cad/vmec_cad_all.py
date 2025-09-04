#Create radial build of stellarator from an existing VMEC input file
import argparse
from rz_convert import *
from radial_from_vmec import *
import json

parser = argparse.ArgumentParser(description="Plot a stellarator configuration from VMEC file.")
parser.add_argument("--file_in", type=str, required=True, help="Name of input file")
parser.add_argument("--config", type=str, required=True, help="Path to JSON config file containing other arguments")

# Parse the arguments
args = parser.parse_args()

# Load JSON configuration
with open(args.config, "r") as json_file:
    config = json.load(json_file)

# Extract values from the JSON configuration
nP = config["nP"]
nT = config["nT"]
t_list = config["t_list"]
b_shape = config["b_shape"]
m_val = config["m_val"]

# Process t_list to convert it into a list of floats
thicknesses = list(map(float, t_list))

# Call VMEC boundary to 3D coord converter
m_axis = np.zeros((nP + 1, 3))
plasma_coords = np.zeros((nP + 1, nT + 1, 3))

# VMEC functionality
MAG_AX(args.file_in, nP, m_axis)
VMEC_RBC_ZBS(args.file_in)
VMEC_TO_RZ("rz_coords.csv", nP, nT, m_val, plasma_coords)

# Build with the parsed arguments
make_build("3D_total.csv", nP, nT, thicknesses, m_axis, b_shape, m_val)
