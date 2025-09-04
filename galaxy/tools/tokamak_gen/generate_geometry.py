"""
This module is used to generate the geometry of a tokamak based on a given configuration file.

The module takes in three command-line arguments: the paths to the configuration file,
the toroidal field (TF) coil file, and the poloidal field (PF) coil file. 

The configuration file is expected to be in JSON format
and contain a 'geometry' key with the following sub-keys: 
'aspect_ratio', 'radial_build', 'component_names', 'TF_dz', 'TF_dr', 'PF_dr', 'PF_dz', 'With_Sol'.

The module reads the configuration file, extracts the geometry data, and assigns them to variables.
It then calculates the major radius and minor radius based on the aspect ratio and radial build.

The module also appends the coil data to the TF and PF coil files. 
The coil data includes the number of turns in the R and Z directions and the current.

Dependencies:
- csv: for writing data to CSV files
- argparse: for parsing command-line arguments
- json: for parsing JSON files
- TokamakGen: for generating the tokamak geometry
"""

# pylint: disable=import-error
import csv
import argparse
import json
import tokamakgen as tg


parser = argparse.ArgumentParser()
parser.add_argument('config_file_path')
parser.add_argument('TF_coil_path')
parser.add_argument('PF_coil_path')
args = parser.parse_args()
config = args.config_file_path
tf_coil_path = args.TF_coil_path
pf_coil_path = args.PF_coil_path
# Open the file and load the data
with open(config, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Now, assign the values to variables
# Assuming your data is under the 'geometry' key
geometry_data = data['geometry']
aspect_ratio = geometry_data['aspect_ratio']
radial_build = geometry_data['radial_build']
component_names = geometry_data['component_names']
TF_dz = geometry_data['TF_dz']
TF_dr = geometry_data['TF_dr']
PF_dr = geometry_data['PF_dr']
PF_dz = geometry_data['PF_dz']
With_Sol = geometry_data['With_Sol']

# output_filename = args.output_filename
print("Solenoid Flag: ", With_Sol)

# radial_build = [0.16, 0.04, 0.03, 0.03, 0.06]
# component_names = ["Plasma", "Vacuum", "First Wall", "Blanket", "Vessel"]
major_rad = aspect_ratio * radial_build[0]
max_a = sum(radial_build)
print(max)

# Init csv
with open(pf_coil_path, "a", newline="", encoding='utf-8') as csvfile:  # 'a' is for append mode
    csv_writer = csv.writer(csvfile)

    csv_writer.writerow(
        [
            "R_turns",
            "Z_turns",
            "I",
            "r_av",
            "dr",
            "dz",
            "coil_x",
            "coil_y",
            "coil_z",
            "normal_x",
            "normal_y",
            "normal_z",
        ]
    )

reactor, coils, radial_build = tg.run_code(
    radial_build,
    component_names,
    aspect_ratio,
    TF_dz,
    TF_dr,
    PF_dz,
    PF_dr,
    With_Sol,
    tf_coil_path,
    pf_coil_path
)

reactor.save("reactor.step")
coils.save("coils.step")
radial_build.save("radial_build.step")
