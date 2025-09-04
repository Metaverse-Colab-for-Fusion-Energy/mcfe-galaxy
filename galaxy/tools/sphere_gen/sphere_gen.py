# pylint: disable=redefined-outer-name
# pylint: disable=import-error
'''
Sphere Generator
Author: Dom Longhorn

This module contains a suite of functions designed to generate spherical geometries 
for fusion reactors. It has the flexibility to create both full spheres and hemispheres, 
and is specifically tailored for Inertial Fusion Energy (IFE) reactors.

Key Features:
- Generate complete reactor layer assemblies based on specified radial builds.
- Option to cut the geometries in half, useful for simulation and visualization.
- Batch processing capabilities to generate multiple reactor geometries with varying parameters.
'''
from math import acos, atan2, degrees
import argparse
import json
import cadquery as cq
import numpy as np


def create_shape(shape, plane_to_cut="XY", cut_in_half=True):
    """
    Creates a shape based on the input parameters. Splits the shape in half if needed.

    Parameters:
        shape: cq.Shape
            The original 3D shape.
        plane_to_cut: str, optional
            The plane to use for cutting the shape in half. Default is "XY".
        cut_in_half: bool, optional
            Whether to cut the shape in half. Default is True.

    Returns:
        halved_shape or shape: cq.Shape
            The modified shape, either cut in half or left whole.
    """
    if cut_in_half:
        cutting_plane = cq.Workplane(plane_to_cut).workplane(offset=10)
        halved_shape = shape.split(cutting_plane.plane)
        return halved_shape

    return shape


def create_reactor_layer(
        radial_build,
        component_names,
        multiplier=1,
        workplane="XY",
        cut_in_half=True,
        hollow_core=True,
        render_save=False,
        save_directory="."):
    """
    Creates a single layer of the reactor based on the provided parameters.

    Parameters:
    radial_build (list): A list of radial dimensions for the reactor core.
    component_names (list): A list of names for the components in the reactor core.
    multiplier (float): A scale factor for the reactor layer dimensions.
    workplane (str): The workplane for the CadQuery model.
    cut_in_half (bool): Whether to cut the reactor layer in half.
    hollow_core (bool, optional): Whether the reactor core is hollow. Defaults to True.
    render_save (bool, optional): Whether to render and save the CadQuery model. Defaults to False.
    save_directory (str, optional): The directory where the CadQuery model should be saved.

    Returns:
    cq.Workplane: A CadQuery Workplane object representing the 3D model of the reactor layer.
    """

    outer_radius = 0
    component_list = []  # Initialize an empty list to hold the components
    for idx, component_thickness in enumerate(radial_build):
        component_thickness *= multiplier
        outer_radius += round(component_thickness, 3)
        if idx == 0:
            sphere = cq.Workplane(workplane).sphere(component_thickness)
        else:
            inner_radius = outer_radius - component_thickness
            sphere = (
                cq.Workplane(workplane)
                .sphere(outer_radius)
                .cut(cq.Workplane(workplane).sphere(inner_radius))
            )

        if idx == 1 and hollow_core:
            print("skipping layer 2")
        else:
            shape = create_shape(
                sphere, plane_to_cut=workplane, cut_in_half=cut_in_half)

            # Add the shape to the component list
            component_list.append(shape)

            if render_save:
                shape.val().exportStep(
                    f"{save_directory}/{component_names[idx]}.step")

    return component_list  # Return the list of components instead of the assembly


def generate_sphere(radial_build,
                    component_names,
                    multipliers=None,
                    workplane="XY",
                    batch=False,
                    cut_in_half=True,
                    hollow_core=True,
                    render_save=False,
                    save_directory="."):
    """
    Generates a 3D model of a spherical reactor based on the provided parameters.

    Parameters:
    radial_build (list): A list of radial dimensions for the reactor core.
    component_names (list): A list of names for the components in the reactor core.
    multipliers (list, optional): A list of scale factors for the reactor layer dimensions.
    workplane (str, optional): The workplane for the CadQuery model. Defaults to "XY".
    batch (bool, optional): Whether to generate a batch of reactors with different scale factors.
    cut_in_half (bool, optional): Whether to cut the reactor in half. Defaults to True.
    hollow_core (bool, optional): Whether the reactor core is hollow. Defaults to True.
    render_save (bool, optional): Whether to render and save the CadQuery model. Defaults to False.
    save_directory (str, optional): The directory where the CadQuery model should be saved.

    Returns:
    cq.Workplane: A CadQuery Workplane object representing the 3D model of the reactor.
    """
    if len(radial_build) != len(component_names):
        raise ValueError(
            "radial_build and component_names must be the same length")

    if multipliers is None:
        multipliers = np.linspace(0.75, 1.5, 10)

    if batch:
        for _ in range(len(radial_build)):
            for multiplier in multipliers:
                reactor = create_reactor_layer(
                    radial_build,
                    component_names,
                    multiplier,
                    workplane,
                    cut_in_half,
                    hollow_core=hollow_core,
                    render_save=render_save,
                    save_directory=save_directory
                )
    else:
        reactor = create_reactor_layer(
            radial_build,
            component_names,
            workplane=workplane,
            cut_in_half=cut_in_half,
            hollow_core=hollow_core,
            render_save=render_save,
            save_directory=save_directory
        )

    return reactor


def add_azimuthal_beamlines(reactor_core_parts, dimensions,
                            layers, radius, use_mini_beamlines=False):
    """
    Adds azimuthal beamlines to the reactor model.

    Parameters:
    reactor (cq.Workplane): The CadQuery Workplane object representing the reactor.
    num_beamlines (int): The number of beamlines to add.
    radius (float): The radius of the beamlines.
    length (float): The length of the beamlines.
    workplane (str, optional): The workplane for the CadQuery model. Defaults to "XY".

    Returns:
    cq.Workplane: The CadQuery Workplane object representing the reactor with added beamlines.
    """
    length, width, height = dimensions
    length = length+radius
    if use_mini_beamlines:
        mini_width, mini_height = width / 2, height / 2
    else:
        mini_width, mini_height = width, height

    num_layers = len(layers)
    polar_angles = np.linspace(0, np.pi, num_layers+2)[1:-1]

    updated_parts = []
    beamlines_list = []
    for part in reactor_core_parts:
        new_part = part  # Start with the original part
        for layer_count, theta in zip(layers, polar_angles):
            phi_step = 2 * np.pi / layer_count

            for i in range(layer_count):
                phi_step_angle = i * phi_step

                x = -radius * np.sin(theta) * np.cos(phi_step_angle)
                y = -radius * np.sin(theta) * np.sin(phi_step_angle)
                z = -radius * np.cos(theta)

                theta_deg = degrees(acos(z / -radius))
                phi_deg = degrees(atan2(y, x))

                num_minis = 4 if use_mini_beamlines else 1
                for dx in np.linspace(-width/4 * (num_minis - 1),
                                      width/4 * (num_minis - 1),
                                      num_minis
                                      ):
                    for dy in np.linspace(-height/4 * (num_minis - 1),
                                          height/4 * (num_minis - 1),
                                          num_minis
                                          ):

                        beamline = cq.Workplane("XY").box(
                            length, mini_width, mini_height, centered=(True, True, True))

                        beamline = beamline.rotate(
                            (0, 0, 0), (0, 1, 0), 90 - theta_deg)
                        beamline = beamline.rotate(
                            (0, 0, 0), (0, 0, 1), phi_deg)

                        mini_x = x + dx * \
                            np.cos(phi_step_angle) - dy * \
                            np.sin(phi_step_angle)
                        mini_y = y + dx * \
                            np.sin(phi_step_angle) + dy * \
                            np.cos(phi_step_angle)

                        beamline = beamline.translate((mini_x, mini_y, z))

                        # Cut this beamline from the new_part
                        new_part = new_part.cut(beamline)

                        # Add the beamline to the list
                        sphere_to_cut = cq.Workplane("XY").sphere(8.48)
                        beamline = beamline.cut(sphere_to_cut)
                        beamlines_list.append(beamline)
        updated_parts.append(new_part)

    return updated_parts, beamlines_list  # Updated reactor parts and the beamlines


parser = argparse.ArgumentParser()
parser.add_argument('file_path')
args = parser.parse_args()
file_path = args.file_path


# Open the file and load the data
with open(file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Now, assign the values to variables
# Assuming your data is under the 'geometry' key
geometry_data = data['geometry']
radial_build = geometry_data['radial_build']
component_names = geometry_data['component_names']
cut_in_half = geometry_data['cut_in_half']
hollow_core = geometry_data['hollow_core']


major_radius = sum(radial_build)

reactor_core_parts = generate_sphere(
    radial_build,
    component_names,
    batch=False,
    cut_in_half=cut_in_half,
    hollow_core=hollow_core,
    render_save=False)
# Add each item from reactor_core list to an assembly

beamline_data = data['beamlines']
gen_beamlines = beamline_data['gen_beamlines']
dimensions = beamline_data['beamline_dimensions']
# Number of beamlines in each azimuthal array
layer_spacing = beamline_data['layer_spacing']
reactor = cq.Assembly()

if gen_beamlines:
    reactor_core, beamlines = add_azimuthal_beamlines(
        reactor_core_parts, dimensions, layer_spacing, major_radius)
    for part in reactor_core:
        reactor.add(part)
    for beamline in beamlines:
        reactor.add(beamline)
else:
    for part in reactor_core_parts:
        print(reactor_core_parts[part])
        reactor.add(part)

reactor.save("reactor.step")
