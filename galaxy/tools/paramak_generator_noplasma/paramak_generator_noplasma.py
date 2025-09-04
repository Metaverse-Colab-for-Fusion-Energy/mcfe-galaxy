import paramak
import numpy as np
import argparse
from stl_to_h5m import stl_to_h5m
import json

parser = argparse.ArgumentParser(
    prog='paramak_generator.py',
    description='Paramak geometry generator'
)

parser.add_argument('config_file', help='Config .txt file with the parameters for the geometry creation. See https://github.com/UoMResearchIT/omniverse-galaxy/tree/main/templates/openmc/paramak_config_MASTER.txt for more details.')
args = parser.parse_args()
config_path = args.config_file


def parametric_blanket(config_dict):
    """
    Function which creates a Blanket, firstwall, divertor and plasma region,
        and outputs a H5M file for OpenMC. ALso returns the plasma
        triangularity and elongation valves to be used when creating the
        plasma in OpenMC.

        Arguments:
            First_wall_thickness : The thickness of the Firstwall of the
                Tokamak(cm)
            Minor_radius: The lenght of the plasma from the centre to the edge
                in a straight line on the x plane (cm)
            Major_radius: The lenght from the (0,0,0) coordinate to the centre
                of the plasma (cm)
            Blanket thickness: Thickness of the blanket (cm)
            Plasma_offset: Distance between the firstwall and the plasma (cm)
            html_output: Creates an 3D html output to view the reactor created
    """

    angle = config_dict["angle_end"] - config_dict["angle_start"]

    plasma = paramak.Plasma(
        minor_radius=config_dict["minor_radius"],
        major_radius=config_dict["major_radius"],
        triangularity=config_dict["triangularity"],
        elongation=config_dict["elongation"],
        rotation_angle=angle,
    )

    firstwall = paramak.BlanketFP(
        plasma=plasma,
        thickness=config_dict["first_wall_thickness"],
        stop_angle=230,
        start_angle=-60,
        offset_from_plasma=config_dict["plasma_offset"],
        rotation_angle=angle,
        num_points=100,
        color=list(np.random.rand(3,))
    )

    # Blanket_cut Shape created to cut the remaining shapes for the divertor
    # Note used in the final reactor

    blanket_cut = paramak.BlanketFP(
        plasma=plasma,
        thickness=config_dict["blanket_thickness"] + config_dict["first_wall_thickness"] + 0.001,  # To make it thicker than the Divertor for cutting
        stop_angle=230,
        start_angle=-60,
        offset_from_plasma=config_dict["plasma_offset"] - config_dict["first_wall_thickness"],  # To make it thicker on the internal dimensions for cutting
        rotation_angle=angle,
    )

    # Blanket Shape created for the final reactor

    blanket = paramak.BlanketFP(
        plasma=plasma,
        thickness=config_dict["blanket_thickness"],
        stop_angle=230,
        start_angle=-60,
        offset_from_plasma=config_dict["plasma_offset"] + config_dict["first_wall_thickness"],
        rotation_angle=angle,
    )

    divertor = paramak.BlanketFP(
        plasma=plasma,
        thickness=config_dict["blanket_thickness"],
        stop_angle=270,
        start_angle=-90,
        offset_from_plasma=config_dict["plasma_offset"] + config_dict["first_wall_thickness"],
        rotation_angle=angle,
        cut=blanket_cut,
        color=list(np.random.rand(3,))
    )

    divertor.export_stl('divertor.stl')
    blanket.export_stl('blanket.stl')
    firstwall.export_stl('firstwall.stl')
    plasma.export_stl('plasma.stl')

    h5m_file = stl_to_h5m(
        files_with_tags=[
            ('divertor.stl', 'divertor'),
            ('blanket.stl', 'blanket'),
            ('firstwall.stl', 'firstwall'),
            #('plasma.stl', 'plasma')
        ],
        h5m_filename='dagmc.h5m'
    )

    return h5m_file, plasma.triangularity, plasma.elongation


if __name__ == "__main__":
    with open(config_path, 'r') as f:
        data = json.load(f)
        config_dict = data['geometry']

    parametric_blanket(config_dict)
