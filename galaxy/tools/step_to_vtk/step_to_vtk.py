# pylint: disable=import-error
"""
This module converts a STEP file to a VTK file using the gmsh library.

It takes an output filename as a command-line argument, loads a STEP file named 'geometry.step',
generates a 3D mesh from the geometry, and writes the mesh to a VTK file.


Usage:
    python step_to_vtk.py <Output_Filename>

Arguments:
    Output_Filename: The name of the output VTK file.

Note:
    This script assumes that a file named 'geometry.step' exists in the same directory.
"""

import os
import argparse
import gmsh


parser = argparse.ArgumentParser()
parser.add_argument("Output_Filename")

args = parser.parse_args()

output_file = args.Output_Filename

# Initialize Gmsh
gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)
gmsh.model.add("modelo_1")


# Load the STEP file
gmsh.merge("geometry.step")

# # Set meshing options
# gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_settings["mesh_max_size"])
# gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_settings["mesh_min_size"])

# Generate the mesh
gmsh.model.mesh.generate(3)

# Save the mesh
gmsh.write("mesh.vtk")
os.rename("mesh.vtk", "output_file.vtk")
