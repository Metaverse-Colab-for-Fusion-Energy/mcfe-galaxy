import openmc
# import os
import math
import numpy as np
import openmc_plasma_source as ops
# import dagmc_h5m_file_inspector as di
# import openmc_tally_unit_converter as otuc
# from openmc_mesh_tally_to_vtk import write_mesh_tally_to_vtk
# import neutronics_material_maker as nmm # To allow importing of pre-defined materials (to see allowed materials - nmm.AvailableMaterials())
import argparse

# EDIT -  better formatting on the help message
parser = argparse.ArgumentParser(
    prog='general_CAD.py',
    description='OpenMC general CAD run script. Useage: python general_CAD.py <geometry file path> <settings file path>'
)

parser.add_argument('geometry_file', help='dagmc.h5m geometry file for simulation')
parser.add_argument('settings_file', help='settings.txt file with the run settings for the simulation')
parser.add_argument('threads', help='number of threads to use for the simulation', type=int)

args = parser.parse_args()

settings_path = args.settings_file
geometry_path = args.geometry_file

# EDIT - NEED TO FIGURE OUT HOW THE IMPROTING OF THE SETTINGS FILE WILL WORK - WHERE TO LOOK FOR IT
# EDIT - And some way to get the geometry_path
# Find the settings file
# sep = os.sep
# path_py = os.path.realpath(__file__)
# settings_path = ''
# geometry_path = ''

# # Find parent folder path
# if "MScDIssertation" in path_py:
#     cwl_folder = path_py.split(f"{sep}MScDIssertation", 1)[0]
# elif "cwl" in path_py:
#     cwl_folder = path_py.split(f"{sep}cwl", 1)[0]

# # Find settings and dagmc files
# for root, dirs, files in os.walk(cwl_folder):
#     for file in files:
#         if file.endswith("settings.txt"):
#             settings_path = os.path.join(root, file)
#         if file.endswith("dagmc.h5m"):
#             geometry_path = os.path.join(root, file)

# EDIT - need settings file location or file information in these formats and then everything else should work...
# Get all settings out
materials_input = []
sources_input = []
boundary_input = []
tallies_input = []
settings_input = []
ex_settings = []
position = 0
with open(settings_path, 'r') as f:
    for line in f:
        if "#" in line:
            continue
        if position == 0:
            if "MATERIALS" in line:
                position = 1
        elif position == 1:
            if "SOURCES" in line:
                position = 2
            else:
                materials_input.append(line.split())
        elif position == 2:
            if "BOUNDARY" in line:
                position = 3
            else:
                sources_input.append(line.split())
        elif position == 3:
            if "SETTINGS" in line:
                position = 4
            else:
                boundary_input.append(line.split())
        elif position == 4:
            if "TALLIES" in line:
                position = 5
            else:
                settings_input.append(line.split())
        elif position == 5:
            if "EXT_SETTINGS" in line:
                position = 6
            else:
                tallies_input.append(line.split())
        elif position == 6:
            ex_settings.append(line.split())


##################
# DEFINE MATERIALS
##################

##########
# TEMP FIX - for eurofer (using in the VV)
##########
# eurofer = nmm.Material.from_library('eurofer').openmc_material()

tmp_material_array = []
for material in materials_input:
    tmp_material = openmc.Material(name=material[0])
    tmp_material.add_element(material[1], 1, "ao")
    tmp_material.set_density("g/cm3", float(material[2]))
    tmp_material_array.append(tmp_material)

materials = openmc.Materials(tmp_material_array)
materials.export_to_xml()

##################
# DEFINE GEOMETRY
##################
# Hack to handle the boundaires for the geometry (for now) - future look at how to handle this
# Took from the paramak examples https://github.com/fusion-energy/magnetic_fusion_openmc_dagmc_paramak_example/blob/main/2_run_openmc_dagmc_simulation.py
dagmc_univ = openmc.DAGMCUniverse(filename=geometry_path)  # EDIT - filename to new filepath - or have it as an argparse string? - need to see in galaxy how best to do this

# creates an edge of universe boundary surface
outer_boundary_radius = boundary_input[0]
vac_surf = openmc.Sphere(r=float(outer_boundary_radius[0]), surface_id=9999, boundary_type="vacuum")  # Normally like 100000

if len(boundary_input) > 1:
    reflective_angle_1 = boundary_input[1]
    reflective_angle_2 = boundary_input[2]
    # adds reflective surface for the sector model at 0 degrees
    reflective_1 = openmc.Plane(
        a=math.sin(math.radians(float(reflective_angle_1[0]))),
        b=-math.cos(math.radians(float(reflective_angle_1[0]))),
        c=0.0,
        d=0.0,
        surface_id=9991,
        boundary_type="reflective",
    )
    # adds reflective surface for the sector model at 90 degrees
    reflective_2 = openmc.Plane(
        a=math.sin(math.radians(float(reflective_angle_2[0]))),
        b=-math.cos(math.radians(float(reflective_angle_2[0]))),
        c=0.0,
        d=0.0,
        surface_id=9990,
        boundary_type="reflective",
    )
    # specifies the region as below the universe boundary and inside the reflective surfaces
    region = -vac_surf & -reflective_1 & +reflective_2
else:
    # just inside the vaccum sphere
    region = -vac_surf

# creates a cell from the region and fills the cell with the dagmc geometry
containing_cell = openmc.Cell(cell_id=9999, region=region, fill=dagmc_univ)

geometry = openmc.Geometry(root=[containing_cell])
geometry.export_to_xml()

##################
# DEFINE SETTINGS
##################

settings = openmc.Settings()

source_type = ''

for ex_setting in ex_settings:
    if ex_setting[0] == "source_type":
        source_type = " ".join(ex_setting[1:])
    else:
        print(f"Don't know what to do with {ex_setting}")

# Sources
# EDIT - need testing for : Fusion Ring Soucre, Fusion Point Source, Point Source
sources = []
angle_conversion = (2*np.pi)/360
if source_type == 'Point Source':  # If a point source
    for source in sources_input:
        source_pnt = openmc.stats.Point(xyz=(float(source[1]), float(source[2]), float(source[3])))
        source = openmc.Source(space=source_pnt, energy=openmc.stats.Discrete(x=[float(source[0]),], p=[1.0,]))
        sources.append(source)
    source_str = 1.0 / len(sources)
    for source in sources:
        source.strength = source_str
    settings.source = sources
elif source_type == 'Fusion Point Source':
    for source in sources_input:
        source_single = ops.FusionPointSource(
            coordinate=(float(source[2]), float(source[3]), float(source[4])),
            temperature=float(source[0]),  # ion temperature in eV
            fuel=str(source[1])  # 'DT' or 'DD'
        )
        sources.append(source_single)
    settings.source = sources
elif source_type == 'Fusion Ring Source':
    # Will only work with one fusion ring source
    source = sources_input[0]
    source_single = ops.FusionRingSource(
        angles=(math.radians(float(source[2])), math.radians(float(source[3]))),
        radius=float(source[0]),
        temperature=float(source[4]),
        fuel=str(source[1]),
        z_placement=float(source[5])
    )
    settings.source = source_single.sources
elif source_type == 'Tokamak Source':
    # Will only work with one tokamak source
    source = sources_input[0]
    source_single = ops.TokamakSource(
        major_radius=float(source[0]),
        minor_radius=float(source[1]),
        elongation=float(source[2]),
        triangularity=float(source[3]),
        mode=str(source[4]),
        angles=(math.radians(float(source[5])), math.radians(float(source[6]))),
        pedestal_radius=0.8 * float(source[1]),

        # below this is not defined properly yet (just pulled from https://github.com/fusion-energy/openmc-plasma-source/blob/main/examples/tokamak_source_example.py)
        ion_density_centre=1.09e20,
        ion_density_peaking_factor=1,
        ion_density_pedestal=1.09e20,
        ion_density_separatrix=3e19,
        ion_temperature_centre=45.9,
        ion_temperature_peaking_factor=8.06,
        ion_temperature_pedestal=6.09,
        ion_temperature_separatrix=0.1,
        shafranov_factor=0.44789,
        ion_temperature_beta=6
    )
    settings.source = source_single.sources
else:
    print(f'I dont know what to do with {source_type}')


# Settings
for setting in settings_input:
    try:
        if setting[0] == "batches":  # Apparently the version of python being used is not new enough for swtich statements... :(
            settings.batches = int(setting[1])
        elif setting[0] == "particles":
            settings.particles = int(setting[1])
        elif setting[0] == "run_mode":
            settings.run_mode = str(" ".join(setting[1:]))
        elif setting[0] == "num_tracks":  # Maximum number of tracks tracked by openMC
            settings.max_tracks = int(setting[1])
        else:
            print(f"Setting: {setting} did not match one of the expected cases.")
    except:
        print(f"There was an error with setting {setting} somewhere...")

settings.export_to_xml()


#############
# TALLIES
#############

ll = tallies_input[0]
ur = tallies_input[1]
size = tallies_input[2]

mesh = openmc.RegularMesh()
mesh.dimension = (int(size[0]), int(size[1]), int(size[2]))
mesh.lower_left = (float(ll[0]), float(ll[1]), float(ll[2]))
mesh.upper_right = (float(ur[0]), float(ur[1]), float(ur[2]))

mesh_filter = openmc.MeshFilter(mesh)

# EDIT - this only works for the heating-local tally currently, not very futureproof - probably want handling for this later
heating_tally = openmc.CellFilter([1])
heating_tally = openmc.Tally(name='heating_on_mesh')
heating_tally.filters = [mesh_filter]
heating_tally.scores = ['heating-local']

tallies = openmc.Tallies([heating_tally])
tallies.export_to_xml()


###########
# RUN
###########

openmc.run(threads=args.threads, tracks=True)  # Run in tracking mode for visualisation of tracks through CAD


# Removing all below this soon as post=processing will be done in another step

# ###############
# # POST-PROCESS
# ###############

# # EDIT - this probably wont be the way this is run in the workflow - potentially as a separate tool for the post processing with the statepoint as an input
# # loads in the statepoint file containing tallies
# statepoint = openmc.StatePoint(filepath="statepoint.3.h5")
# tally_to_convert = statepoint.get_tally(name="heating_on_mesh")

# # write_mesh_tally_to_vtk(tally=tally_to_convert, filename='vtk_from_mesh.vtk')

# # From https://github.com/fusion-energy/openmc_tally_unit_converter/blob/main/examples/processing_3d_mesh_heating_tally.py
# # this finds the number of neutrons emitted per second by a 3MW fusion DT plasma
# source_strength = otuc.find_source_strength(
#     fusion_energy_per_second_or_per_pulse=3e6, reactants="DT"
# )

# # scaled from picosievert to sievert
# result, error = otuc.process_tally(
#     tally=tally_to_convert,
#     required_units="watts / mm ** 3",
#     source_strength=source_strength,  # number of neutrons per second emitted by the source
# )

# result_dict = {
#     "heating-local": np.array(result)
# }

# # EDIT - what output is more useful, a CSV or VTK with mesh locations on? - probably vtk at a guess
# mesh.write_data_to_vtk('output.vtk', result_dict)

# # array = np.array(result) # For saving as csv
# # np.savetxt('output.csv', array, delimiter=",")


# '''
# TODO:
#     - Add input tests for correct input types
#     - Add error handling with good error messages
#     - Actually test...
#     - Change all the areas that start with EDIT...
# '''
