"""
This module contains the `create_geometry_and_mesh` function which is used for
creating and meshing a cylindrical geometry using the gmsh Python API.

The function takes a dictionary of cylinder data as input, which includes the
number of layers in the cylinder and a mesh factor for controlling the mesh
density. It then creates the geometry of the cylinder, applies the mesh, and
creates physical groups for the surfaces and volumes of the cylinder.

The module also includes functionality for parsing command-line arguments and
reading parameters from a JSON file. This allows the cylinder data to be easily
specified and modified.

Dependencies:
    argparse: A standard library module for parsing command-line arguments.
    json: A standard library module for working with JSON data.
    os: A standard library module for interacting with the operating system.
    gmsh: A Python library for scripting Gmsh, a 3D finite element mesh generator.

Author: Luis Garcia
"""

import argparse
import json
import os
import gmsh


def create_geometry_and_mesh(cylinder_data):
    """
    Creates and meshes a cylindrical geometry using the gmsh Python API.

    Parameters:
    cylinder_data (dict): A dictionary containing the number of layers in the 
    cylinder and a mesh factor for controlling the mesh density.

    Returns:
    None: The function creates the geometry and mesh, but does not return any value.
    """
    gmsh.initialize()
    gmsh.model.add("cylinder_model")

    step_file = "reactor.step"
    num_layers = cylinder_data['num_layers']
    mesh_factor = cylinder_data['mesh_factor']

    gmsh.option.setNumber("Mesh.CharacteristicLengthFactor", mesh_factor)
    gmsh.option.setNumber("Mesh.Algorithm", 1)  # Delaunay
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)  # 3D algorithm

    # Import STEP file
    gmsh.model.occ.importShapes(step_file)

    # Synchronize necessary due to use of OpenCASCADE
    gmsh.model.occ.synchronize()

    j = 1  # Initial tag offset

    # Creating physical groups for surfaces
    for i in range(1, num_layers + 1):
        wall_tag = i * 3 - 2  # Wall is the long length of cylinder
        top_tag = i * 3 - 1   # Top circular face
        bottom_tag = i * 3    # Bottom circular face

        if i <= 2:
            gmsh.model.addPhysicalGroup(2, [wall_tag], wall_tag)
            gmsh.model.setPhysicalName(2, wall_tag, f"cyl_{i}_wall")
            gmsh.model.addPhysicalGroup(2, [top_tag], top_tag)
            gmsh.model.setPhysicalName(2, top_tag, f"cyl_{i}_top")
            gmsh.model.addPhysicalGroup(2, [bottom_tag], bottom_tag)
            gmsh.model.setPhysicalName(2, bottom_tag, f"cyl_{i}_bottom")
        else:
            gmsh.model.addPhysicalGroup(2, [wall_tag + j], wall_tag + j)
            gmsh.model.setPhysicalName(2, wall_tag, f"cyl_{i}_wall")
            gmsh.model.addPhysicalGroup(2, [top_tag + j], top_tag + j)
            gmsh.model.setPhysicalName(2, top_tag, f"cyl_{i}_top")
            gmsh.model.addPhysicalGroup(2, [bottom_tag + j], bottom_tag + j)
            gmsh.model.setPhysicalName(2, bottom_tag, f"cyl_{i}_bottom")
            j += 1

    for i in range(1, num_layers + 1):
        volume_tag = i
        gmsh.model.addPhysicalGroup(3, [volume_tag], tag=i)
        gmsh.model.setPhysicalName(3, i, f"cyl_{i}_volume")

    # Generate mesh
    gmsh.model.mesh.generate(3)

    # Save mesh (optional, uncomment to save)
    gmsh.write("meshed_model.msh")

    gmsh.finalize()


# Main script
parser = argparse.ArgumentParser()
parser.add_argument('file_path')
args = parser.parse_args()
file_path = args.file_path

with open(file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

cylinder_data_input = data['cylinder_data']
create_geometry_and_mesh(cylinder_data_input)


os.rename("meshed_model.msh", "outputfile.msh")
