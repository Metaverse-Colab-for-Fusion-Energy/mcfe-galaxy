"""
NOTE:
    This is a very temporary script to test the full workflow running from paramak generator to openmc to PINN
    Will be replacecd with the new JSON set of scripts once they are ready
"""
import math
import os
import openmc
from openmc_plasma_source import TokamakSource
import neutronics_material_maker as nmm

import json
import argparse

parser = argparse.ArgumentParser(
    prog='openmc_parametric.py',
    description='OpenMC parametric CAD run script. Useage: python openmc_parametric.py <geometry file path> <config file path> <unstructured_mesh_file> <statepoint output file path>'
)

parser.add_argument('geometry_file', help='dagmc.h5m geometry file for simulation. Format: h5m')
parser.add_argument('config_file', help='config.json file with the run settings for the simulation. Format: JSON')
parser.add_argument('unstructured_mesh_file', help='unstructured mesh file for the simulation. Format: h5m')
parser.add_argument('statepoint_file', help='statepoint.h5 file for the simulation. Format: h5')
parser.add_argument('threads', help='number of threads to use for the simulation', type=int)

args = parser.parse_args()

geom_path = args.geometry_file
config_path = args.config_file
unstructured_mesh_path = args.unstructured_mesh_file
statepoint_path = args.statepoint_file
# Import the config file
with open(config_path, 'r') as read_f:
    config = json.load(read_f)

# Seperate the categories in the config file (easier now than individually later)
materials = config['materials']
geometry = config['geometry']
settings = config['settings']
tallies = config['tallies']

# BIG TODO:
#     Material input - checking the inputs
#                    - better handling of some of the fields here too (enrichement...)
#     Check if the different inputs need to be specified type, e.g. float(dict['key'])

"""
    Arguments:
    h5m_inputfile: The file containing the cad model of the blanket region. str
    enrichment: The Value of the Lithium-6 enrichment percentage
    Blanket_materials: The material each layer is made from. Uses the neutronics material maker package for names of each input material refer to https://neutronics-material-maker.readthedocs.io/en/latest/
    firstwall_material: The material of the firstwall. Uses the neutronics material maker package for names of each input material refer to https://neutronics-material-maker.readthedocs.io/en/latest/
    Structure_volume_percentage: The Decimal  ratio of each material in order of Blanket, Structure, Coolant
    Temperature: Temperature of the Blanket region. float
    minor_radius: Minor radius of the Tokamak (cm)
    major_radius: Major radius of the Tokamak (cm)
"""

model = openmc.model.Model()

########################################
# MATERIALS
########################################

material_array = []
for key, value in materials.items():  # TODO: This currently doesn't handle just a single enriched material (need option for this at somepoint)
    print(key)
    if len(value) == 1:  # Case that there is no mixture of material
        temp_material = nmm.Material.from_library(
            name=list(value.keys())[0],
            temperature=settings['temperature'],
        ).openmc_material

        # Checking for now TODO: is there anything to enforce that this is deffo 100% in a better manner
        if list(value.values())[0] == 100:
            print(f'Good {key}')
        else:
            print(f"Bad {key}")

    else:  # Mixture case
        mix_material_array = []
        frac_array = []

        for sub_key, sub_value in value.items():
            if isinstance(sub_value, int) or isinstance(sub_value, float):  # Case for no enrichment
                temp_mix_material = nmm.Material.from_library(
                    name=sub_key,
                    temperature=settings['temperature'],
                ).openmc_material
                frac_array.append(sub_value/100)
            else:  # Enrichment case
                # sub_value format: [<frac (float)>, <enrichment (float)>, <enrichment_target (string)>]
                temp_mix_material = nmm.Material.from_library(
                    name=sub_key,
                    enrichment=sub_value[1],
                    enrichment_target=sub_value[2],
                    enrichment_type='wo',  # TODO: Check this is correct with Adam (if not can add to JSON)
                    temperature=settings['temperature'],
                ).openmc_material
                frac_array.append(sub_value[0]/100)
            mix_material_array.append(temp_mix_material)

        if sum(frac_array) == 1:
            print(f"Good {key}")
        else:
            print(f"Bad {key}")
            print(sum(frac_array))
            print(frac_array)

        temp_material = nmm.Material.from_mixture(
            materials=mix_material_array,
            fracs=frac_array,
            percent_type='vo'
        ).openmc_material

        mixture_index = len(material_array)

    temp_material.name = key
    material_array.append(temp_material)

# Add materials to model
materials = openmc.Materials(material_array)
model.materials = materials

########################################
# CREATE GEOMETRY & BOUNDARY CONDITIONS
########################################

# Create universe with the input file
dag_univ = openmc.DAGMCUniverse(filename=geom_path)
vac_surf = openmc.Sphere(r=geometry['outer_sphere'], surface_id=9999, boundary_type="vacuum")

# Adds reflective surface for the sector model at 0 degrees
reflective_1 = openmc.Plane(
    a=math.sin(math.radians(geometry['angle_start'])),
    b=-math.cos(math.radians(geometry['angle_start'])),
    c=0.0,
    d=0.0,
    surface_id=9991,
    boundary_type="reflective",
)

# Adds reflective surface for the sector model at 90 degrees
reflective_2 = openmc.Plane(
    a=math.sin(math.radians(geometry['angle_end'])),
    b=-math.cos(math.radians(geometry['angle_end'])),
    c=0.0,
    d=0.0,
    surface_id=9990,
    boundary_type="reflective",
)

# Specifies the region as below the universe boundary and inside the reflective surfaces
region = -vac_surf & -reflective_1 & +reflective_2

# Creates a cell from the region and fills the cell with the dagmc geometry
containing_cell = openmc.Cell(cell_id=9998, region=region, fill=dag_univ)

geom = openmc.Geometry(root=[containing_cell])
model.geometry = geom

########################################
# SOURCE
########################################

source = TokamakSource(
    elongation=geometry['elongation'],
    ion_density_centre=1.09e20,
    ion_density_peaking_factor=1,
    ion_density_pedestal=1.09e20,
    ion_density_separatrix=3e19,
    ion_temperature_centre=45.9,
    ion_temperature_peaking_factor=8.06,
    ion_temperature_pedestal=6.09,
    ion_temperature_separatrix=0.1,
    major_radius=geometry['major_radius'],
    minor_radius=geometry['minor_radius'],
    pedestal_radius=0.8 * geometry['minor_radius'],
    mode="H",
    shafranov_factor=0.44789,
    triangularity=geometry['triangularity'],
    ion_temperature_beta=6,
    angles=(math.radians(geometry['angle_start']), math.radians(geometry['angle_end'])),
    sample_size=100  # TODO: Add this to the config file
)

model.settings.source = source.sources

########################################
# TALLIES
########################################

mesh = openmc.UnstructuredMesh(unstructured_mesh_path, library='moab')


mesh_filter = openmc.MeshFilter(mesh)

# EDIT - this only works for the heating-local tally currently, not very futureproof - probably want handling for this later
heating_tally = openmc.CellFilter([1])
heating_tally = openmc.Tally(name='heating_on_mesh')
heating_tally.filters = [mesh_filter]
heating_tally.scores = ["heating-local"]

tallies = openmc.Tallies([heating_tally])
model.tallies = tallies

########################################
# RUN SETTINGS
########################################

model.settings.batches = settings['batches']
model.settings.particles = settings['particles']
model.settings.run_mode = settings['run_mode']
model.settings.max_tracks = settings['num_tracks']
model.settings.output = {'tallies': False}

model.settings.dagmc = True

########################################
# RUN MODEL
########################################

sp_file = model.run(threads=args.threads)

os.system(f"mv {sp_file} {statepoint_path}")  # TEMP FIX
