import math
import openmc
from openmc_plasma_source import TokamakSource
import neutronics_material_maker as nmm
import os

import json
import argparse


# HCPB HCLL WCLL DCLL are presets for premade blanket designs
def HCPB(Temperature):
    mat_Blanket = nmm.Material.from_library(
        name="Li4SiO4",
        enrichment=60.0,
        enrichment_target="Li6",
        temperature=Temperature,
    ).openmc_material

    mat_Structure = nmm.Material.from_library(
        name="eurofer", temperature=700
    ).openmc_material

    mat_Coolant = nmm.Material.from_library(
        name="Helium, Natural", temperature=Temperature
    ).openmc_material
    mat_Multipler = nmm.Material.from_library(
        name="Be", temperature=Temperature
    ).openmc_material

    mat_Mixture_in = nmm.Material.from_mixture(
        materials=[mat_Blanket, mat_Structure, mat_Coolant, mat_Multipler],
        fracs=[0.097, 0.098, 0.369, 0.436],
        percent_type="vo",
    ).openmc_material
    mat_Mixture_in.name = "Blanket_inboard"

    mat_Mixture_out = nmm.Material.from_mixture(
        materials=[mat_Blanket, mat_Structure, mat_Coolant, mat_Multipler],
        fracs=[0.097, 0.098, 0.369, 0.436],
        percent_type="vo",
    ).openmc_material
    mat_Mixture_out.name = "Blanket_outboard"

    return mat_Mixture_in, mat_Mixture_out


def HCLL(Temperature):
    mat_Blanket = nmm.Material.from_library(
        name="lithium-lead",
        enrichment=90.0,
        enrichment_target="Li6",
        temperature=Temperature,
    ).openmc_material

    mat_Structure = nmm.Material.from_library(
        name="eurofer", temperature=Temperature
    ).openmc_material

    mat_Coolant = nmm.Material.from_library(
        name="Helium, Natural", temperature=Temperature
    ).openmc_material

    mat_Mixture_in = nmm.Material.from_mixture(
        materials=[mat_Blanket, mat_Structure, mat_Coolant],
        fracs=[0.85, 0.07, 0.08],
        percent_type="vo",
    ).openmc_material
    mat_Mixture_in.name = "Blanket_inboard"

    mat_Mixture_out = nmm.Material.from_mixture(
        materials=[mat_Blanket, mat_Structure, mat_Coolant],
        fracs=[0.85, 0.07, 0.08],
        percent_type="vo",
    ).openmc_material
    mat_Mixture_out.name = "Blanket_outboard"

    return mat_Mixture_in, mat_Mixture_out


def WCLL(Temperature):
    mat_Blanket = nmm.Material.from_library(
        name="lithium-lead",
        enrichment=90.0,
        enrichment_target="Li6",
        temperature=Temperature,
    ).openmc_material

    mat_Structure = nmm.Material.from_library(
        name="eurofer", temperature=Temperature
    ).openmc_material

    mat_Coolant = nmm.Material.from_library(
        name="Water, Vapor", temperature=Temperature
    ).openmc_material

    mat_Mixture_in = nmm.Material.from_mixture(
        materials=[mat_Blanket, mat_Structure, mat_Coolant],
        fracs=[0.85, 0.1, 0.05],
        percent_type="vo",
    ).openmc_material
    mat_Mixture_in.name = "Blanket_inboard"

    mat_Mixture_out = nmm.Material.from_mixture(
        materials=[mat_Blanket, mat_Structure, mat_Coolant],
        fracs=[0.85, 0.1, 0.05],
        percent_type="vo",
    ).openmc_material
    mat_Mixture_out.name = "Blanket_outboard"

    return mat_Mixture_in, mat_Mixture_out


def DCLL(Temperature):
    mat_Blanket = nmm.Material.from_library(
        name="lithium-lead",
        enrichment=90.0,
        enrichment_target="Li6",
        temperature=Temperature,
    ).openmc_material

    mat_Structure = nmm.Material.from_library(
        name="eurofer", temperature=Temperature
    ).openmc_material

    mat_Coolant = nmm.Material.from_library(
        name="Helium, Natural", temperature=Temperature
    ).openmc_material

    mat_insulator = nmm.Material.from_library(
        name="SiC", temperature=Temperature
    ).openmc_material

    mat_Mixture_in = nmm.Material.from_mixture(
        materials=[mat_Blanket, mat_Structure, mat_Coolant, mat_insulator],
        fracs=[0.85, 0.08, 0.03, 0.04],
        percent_type="vo",
    ).openmc_material
    mat_Mixture_in.name = "Blanket_inboard"

    mat_Mixture_out = nmm.Material.from_mixture(
        materials=[mat_Blanket, mat_Structure, mat_Coolant, mat_insulator],
        fracs=[0.85, 0.08, 0.03, 0.04],
        percent_type="vo",
    ).openmc_material
    mat_Mixture_out.name = "Blanket_outboard"

    return mat_Mixture_in, mat_Mixture_out


# Create a scatter tally from a material filter
def ScatterTally(material_filter, name):
    neutron_particle_filter = openmc.ParticleFilter(["neutron"])
    material_scatter_tally = openmc.Tally(
        name=("Scatter_" + str(name))
    )
    material_scatter_tally.scores = ["scatter"]
    material_scatter_tally.filters = [
        material_filter, neutron_particle_filter
    ]

    return material_scatter_tally


# Create an absorption tally from a material filter
def AbsorptionTally(material_filter, name):
    neutron_particle_filter = openmc.ParticleFilter(["neutron"])
    material_absorption_tally = openmc.Tally(
        name=("Absorption_" + str(name))
    )
    material_absorption_tally.scores = ["absorption"]
    material_absorption_tally.filters = [
        material_filter, neutron_particle_filter
    ]

    return material_absorption_tally


# Create a Muliplication tally from a material filter
def MultiplicationTally(material_filter, name):
    neutron_particle_filter = openmc.ParticleFilter(["neutron"])
    material_multiplication_tally = openmc.Tally(
        name=("Multiplication_" + str(name))
    )
    material_multiplication_tally.scores = ["(n,2n)"]
    material_multiplication_tally.filters = [
        material_filter, neutron_particle_filter
    ]

    return material_multiplication_tally


# TBR Tally from material filter
def TBRTally(material_filter, name):
    tbr_tally = openmc.Tally(
        name=(f"TBR_{name}")
    )
    tbr_tally.filters = [material_filter]
    tbr_tally.scores = ["(n,Xt)"] # Trigger doesnt work for H3-production score changed to equivalent

    return tbr_tally


def openmc_model(config_dict, geom_path, statepoint_path, threads):
    """Creates a Model of the h5m file from Paramak_H5M_creater.
        This Model will be used to drive neutronic simulations

    Arguments:
       h5m_inputfile: The file containing the cad model of the blanket region.
        str
       Firstwall: Material of the Firstwall must be from Neutronics Material
        maker format. str
       Blanket_type: Type of Blanket resets ('HCPB','WCLL', 'HCLL', 'DCLL')
        Also 'User' can be used but Blanket_Breeder must be inputted]. str
       Inboard_Structure_Blanket: List containing Material name, coolant name
        (from Neutronics Material maker) and fractions of volumes(0.8,0.2). arr
       Outboard_Structure_Blanket: List containing Material name, coolant name
        (from Neutronics Material maker) and fractions of volumes(0.8,0.2). arr
       Blanket_Manifold: List containing Material name, coolant name (from
        Neutronics Material maker) and fractions of volumes(0.8,0.2). list
       Divertor: Material of the Divertor must be from Neutronics Material
        maker format. str
       Plasma_elongation: Use the same value as used to create the H5M file.
        float
       Plasma_triangularity: Use the same value as used to create the H5M file.
        float
       Temperature: Temperature of all components. float
       minor_radius: Use the same value as used to create the H5M file. float
       major_radius: Use the same value as used to create the H5M file. float
       Reflector: Material of the Reflector must be from Neutronics Material
        maker format. Use None if no reflector was used when creating the H5M
        files. str
       Multiplier: Material of the Multiplier must be from Neutronics Material
        maker format. Use None if no reflector was used when creating the H5M
        files. str
       Blanket_Breeder: Must be used if Blanket_type = 'User'. List containing
        Material name, coolant name (from Neutronics Material maker), fractions
        of volumes(0.8,0.2) and lithium 6 enrichment. list
    """
    model = openmc.model.Model()
 
    materials = config_dict["materials"]
    geometry = config_dict["geometry"]
    settings = config_dict["settings"]
    source = config_dict["source"]
    tally = config_dict['tally']

    #############
    # Create MATERIALS
    #############
    # A list to collect all created materials
    Collect_Materials = []
    # A list to collect all materials, used for tallies
    material_lookup = []

    for key, value in materials.items():
        # TODO: This currently doesn't handle just a single enriched material
        # (need option for this at somepoint)
        print(key)
        if settings['blanket_type'] != 'User' and (key == 'Blanket_inboard' or key == 'Blanket_outboard'):
            continue

        # Assume everything is a mix of materials
        mix_material_array = []
        frac_array = []

        for mat_name, mat_properties in value.items():
            # Case for no enrichment
            if mat_properties['enriched'] is False:
                temp_mix_material = nmm.Material.from_library(
                    name=mat_name,
                    temperature=settings['temperature'],
                ).openmc_material
                frac_array.append(mat_properties['mixture_amount']/100)
            # Case for enrichment
            else:
                # sub_value format:
                # [<frac%>, <enrichment%>, <enrichment_target>]
                temp_mix_material = nmm.Material.from_library(
                    name=mat_name,
                    enrichment=mat_properties['enrichment_amount'],
                    enrichment_target=mat_properties['enrichment_target'],
                    # TODO: Check this is correct with Adam
                    enrichment_type='wo',
                    temperature=settings['temperature'],
                ).openmc_material
                frac_array.append(mat_properties['mixture_amount']/100)
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

        temp_material.name = key
        Collect_Materials.append(temp_material)
        material_lookup.append([key, temp_material])

    # Create dictionary to call the appropriate function and check JSON input
    blanket_type_dict = {
        "HCPB": HCPB,
        "HCLL": HCLL,
        "WCLL": WCLL,
        "DCLL": DCLL,
    }

    # Get the type from the JSON and select the function
    selected_blanket = blanket_type_dict.get(settings['blanket_type'])

    if selected_blanket:
        Blanket_mat_in, Blanket_mat_out = selected_blanket(settings['temperature'])
        Collect_Materials.extend([Blanket_mat_in, Blanket_mat_out])

        for material in [Blanket_mat_in, Blanket_mat_out]:
            material_lookup.append([str(material.name), material])
    else:
        if settings['blanket_type'] == "User":
            print("User Blanket type selected")
        else:
            print("""Incorrect Blanket type, options:
                HCPB, HCLL, WCLL, DCLL or User""")

    # Combine all materials
    materials = openmc.Materials(Collect_Materials)
    model.materials = materials

    ########################################
    # CREATE GEOMETRY & BOUNDARY CONDITIONS
    ########################################

    # Create universe with the input file
    dag_univ = openmc.DAGMCUniverse(filename=geom_path)
    vac_surf = openmc.Sphere(
        r=geometry['outer_sphere'],
        surface_id=9999,
        boundary_type="vacuum"
    )

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

    # Sim region in the universe boundary and the reflective surfaces
    region = -vac_surf & -reflective_1 & +reflective_2

    # Creates a cell from the region and fills the cell with the dagmc geometry
    containing_cell = openmc.Cell(cell_id=9998, region=region, fill=dag_univ)

    geom = openmc.Geometry(root=[containing_cell])
    model.geometry = geom

    ########################################
    # SOURCE
    ########################################

    # Source type
    if source['type'] == "tokamak source":
        source = TokamakSource(
            elongation=geometry['elongation'],
            ion_density_centre=1.09e20,
            ion_density_peaking_factor=1,
            ion_density_pedestal=1.09e20,
            ion_density_separatrix=3e19,
            ion_temperature_centre=source['central_ion_temp'],
            ion_temperature_peaking_factor=8.06,
            ion_temperature_pedestal=6.09,
            ion_temperature_separatrix=0.1,
            major_radius=geometry['major_radius'],
            minor_radius=geometry['minor_radius'],
            pedestal_radius=0.8 * geometry['minor_radius'],
            mode=geometry['mode'],
            shafranov_factor=0.44789,
            triangularity=geometry['triangularity'],
            ion_temperature_beta=6,
            angles=(
                math.radians(geometry['angle_start']),
                math.radians(geometry['angle_end'])
            ),
            sample_size=100  # TODO: Add this to the config file
        )
    else:
        print("Incorrect Source type, input must be a string of source type")
        print(f'Input was {source["type"]}')

    model.settings.source = source.sources

    ########################################
    # TALLIES
    ########################################
    scatter_tally_materials = tally['scatter_tally_materials']
    absorbtion_tally_materials = tally['absorbtion_tally_materials']
    multiplication_tally_materials = tally['multiplication_tally_materials']
    tbr_tally_materials = tally['tbr_tally_materials']

    Tally_collect = []  # A list to collect all the tallies used

    for material in material_lookup:
        material_filter = openmc.MaterialFilter(material[1])

        if material[0] in scatter_tally_materials:
            scatter_tally = ScatterTally(
                material_filter=material_filter,
                name=material[1].name
            )
            Tally_collect.append(scatter_tally)

        if material[0] in absorbtion_tally_materials:
            absorbtion_tally = AbsorptionTally(
                material_filter=material_filter,
                name=material[1].name
            )
            Tally_collect.append(absorbtion_tally)

        if material[0] in multiplication_tally_materials:
            multiplication_tally = MultiplicationTally(
                material_filter=material_filter,
                name=material[1].name
            )
            Tally_collect.append(multiplication_tally)

        if material[0] in tbr_tally_materials:
            tbr_tally = TBRTally(
                material_filter=material_filter,
                name=material[1].name
            )
            Tally_collect.append(tbr_tally)

    # Add to model
    model.tallies = openmc.Tallies(Tally_collect)

    ########################################
    # SETTINGS
    ########################################
    model.settings.batches = settings['batches']
    model.settings.particles = settings['particles']
    model.settings.run_mode = settings['run_mode']
    model.settings.output = {'tallies': False}
    # Do we want this static or variable from JSON?
    model.settings.temperature = {"method": "interpolation"}
    print(f"Threads: {threads}")
    sp_file = model.run(threads=threads)
    # return model & save to results.h5 so the tool can pick it up
    os.system(f"mv {sp_file} {statepoint_path}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog='openmc_parametric.py',
        description='''OpenMC parametric CAD run script.
        Useage: python openmc_parametric.py <geom_f> <config_f> <sp_f>'''
    )

    parser.add_argument(
        'geometry_file',
        help='dagmc.h5m geometry file for simulation'
    )
    parser.add_argument(
        'config_file',
        help='config.json file with the run settings for the simulation'
    )
    parser.add_argument(
        'statepoint_file',
        help='Output file to save the statepoint to. Format: h5'
    )
    parser.add_argument(
        'threads',
        help='Number of threads to use for the simulation. Format: int'
    )
    args = parser.parse_args()

    geom_path = args.geometry_file
    config_path = args.config_file
    statepoint_path = args.statepoint_file
    threads = args.threads

    with open(config_path, "r") as config_file:
        config_dict = json.load(config_file)

    openmc_model(config_dict, geom_path, statepoint_path, threads)
