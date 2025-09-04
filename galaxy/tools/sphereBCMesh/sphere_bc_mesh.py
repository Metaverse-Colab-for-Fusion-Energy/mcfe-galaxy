# pylint: disable=import-error
"""
This module uses the gmsh library to create a 3D mesh from a STEP file.

The module takes a dictionary of sphere data and geometry data as input. 
The sphere data includes the number of layers in the sphere and a mesh factor. 
The geometry data includes whether the sphere is cut in half and whether it has a hollow core.

The module initializes a gmsh model, imports the STEP file, and sets various mesh options. 
It then creates physical groups for each layer of the sphere, and if the sphere is cut in half, 
it creates additional physical groups for each half.

Functions:
    create_geometry_and_mesh(sphere_data, geometry): Creates a 3D mesh from a STEP file using gmsh.

Usage:
    import GMSHsphereBCMesh
    sphere_data = {'num_layers': 3, 'mesh_factor': 0.1}
    geometry = {'cut_in_half': True, 'hollow_core': False}
    GMSHsphereBCMesh.create_geometry_and_mesh(sphere_data, geometry)

Note:
    This script assumes that a file named 'reactor.step' exists in the same directory.
"""

import argparse
import json
import os
import gmsh


def create_geometry_and_mesh(sphere_data, geometry):
    """
    Creates a 3D mesh from a STEP file using gmsh.

    This function initializes a gmsh model, imports a STEP file, sets various mesh options, 
    and creates physical groups for each layer of the sphere. If the sphere is cut in half, 
    it creates additional physical groups for each half.

    Parameters:
    sphere_data (dict): 
    A dictionary containing the number of layers in the sphere and a mesh factor.
    geometry (dict):
    A dictionary containing whether the sphere is cut in half and whether it has a hollow core.

    Returns:
    None
    """
    gmsh.initialize()
    gmsh.model.add("sphere_model")

    step_file = "reactor.step"
    num_layers = sphere_data['num_layers']
    mesh_factor = sphere_data['mesh_factor']
    cut_in_half = geometry['cut_in_half']
    hollow_core = geometry['hollow_core']

    gmsh.option.setNumber("Mesh.CharacteristicLengthFactor", mesh_factor)
    gmsh.option.setNumber("Mesh.Algorithm", 1)  # Delaunay
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)  # 3D algorithm

    # Import STEP file
    gmsh.model.occ.importShapes(step_file)

    # Synchronize necessary due to use of OpenCASCADE
    gmsh.model.occ.synchronize()

    # Creating physical groups
    if not hollow_core:
        for i in range(1, num_layers+1):
            volume_tag = i
            gmsh.model.addPhysicalGroup(3, [volume_tag], tag=i)
            gmsh.model.setPhysicalName(3, i, f"sph_{i}_volume")
    else:
        for i in range(1, num_layers):
            volume_tag = i
            gmsh.model.addPhysicalGroup(3, [volume_tag], tag=i)
            gmsh.model.setPhysicalName(3, i, f"sph_{i+1}_volume")
    if cut_in_half:
        for i in range(1, num_layers+1):
            sphere_tag = (i * 2) - 1
            plane_tag = i * 2
            if i <= 2:
                gmsh.model.addPhysicalGroup(2, [sphere_tag], tag=sphere_tag)
                gmsh.model.setPhysicalName(2, sphere_tag, f"sph_{i}_sphere")
                gmsh.model.addPhysicalGroup(2, [plane_tag], tag=plane_tag)
                gmsh.model.setPhysicalName(2, plane_tag, f"sph_{i}_plane")
            else:
                adjusted_tag = 3 * (i - 1)
                gmsh.model.addPhysicalGroup(2, [adjusted_tag], tag=sphere_tag)
                gmsh.model.setPhysicalName(2, sphere_tag, f"sph_{i}_sphere")
                gmsh.model.addPhysicalGroup(
                    2, [adjusted_tag + 1], tag=plane_tag)
                gmsh.model.setPhysicalName(2, plane_tag, f"sph_{i}_plane")
    else:
        for i in range(1, num_layers+1):
            sphere_tag = i
            adjusted_tag = (i * 2) - 2
            if i <= 2:
                gmsh.model.addPhysicalGroup(2, [sphere_tag], tag=sphere_tag)
                gmsh.model.setPhysicalName(2, sphere_tag, f"sph_{i}_sphere")
            else:
                gmsh.model.addPhysicalGroup(2, [adjusted_tag], tag=sphere_tag)
                gmsh.model.setPhysicalName(2, sphere_tag, f"sph_{i}_sphere")

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

mesh_information = data['sphere_data']
geometry_info = data['geometry']
create_geometry_and_mesh(mesh_information, geometry_info)


os.rename("meshed_model.msh", "outputfile.msh")
