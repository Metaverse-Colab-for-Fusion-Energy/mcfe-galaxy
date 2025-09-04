import gmsh
import numpy as np
import json
import argparse

parser = argparse.ArgumentParser(
    prog="sample_points_PINN.py",
    description="Create samplem points and mesh for PINN workflow. Useage: python sample_points_PINN.py <config file path> <output points>",
)

parser.add_argument(
    "config_file", help="JSON file with meshing settings (in ['mesh_settings']). Format: JSON"
)
parser.add_argument("points_file", help="Location to save the output points file to. Format: txt")

args = parser.parse_args()

config_path = args.config_file
points_path = args.points_file


# Import the config file
with open(config_path, "r") as read_f:
    config = json.load(read_f)

mesh_settings = config["mesh_settings"]

# Initialize Gmsh
gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)
gmsh.model.add("modelo_1")

# Load the STEP file
gmsh.merge("input.stl")

# Set meshing options
gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_settings["mesh_max_size"])
gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_settings["mesh_min_size"])

# Generate the mesh
gmsh.model.mesh.generate(3)

# Save the mesh
gmsh.write("mesh.vtk")

# Save the coordinates to a text file
coord_set = gmsh.model.mesh.getNodes()
coords = np.array(coord_set[1]).reshape(-1, 3)

with open(points_path, "w") as f:
    for x, y, z in coords:
        f.write(f"{x} {y} {z}\n")

# Finalize Gmsh
gmsh.finalize()
