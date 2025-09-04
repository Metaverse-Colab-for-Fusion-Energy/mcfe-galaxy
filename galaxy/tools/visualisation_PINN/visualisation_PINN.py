import vtk
import numpy as np
import pickle
import argparse

parser = argparse.ArgumentParser(
    prog="visualisation_PINN.py",
    description="Program to take the results of a PINN simulation and visualise them in a Paraview readable format. Useage: python visualisation_PINN.py <pinn_input> <mesh_input> <output_file>",
)

parser.add_argument(
    "pinn_file", help="input.npz file with the results of the PINN simulation"
)
parser.add_argument(
    "mesh_file", help="mesh.vtk file with the geometry for the visualisation - from sample points generator"
)
parser.add_argument(
    "output_file", help="output.vtk file with the visualisation of the PINN simulation"
)

args = parser.parse_args()

pinn_path = args.pinn_file
mesh_path = args.mesh_file
output_path = args.output_file

# Load the .npz file with allow_pickle=True to support protocol 3
data = np.load(pinn_path, allow_pickle=True)

# Access the array using the key 'arr_0' (replace with the actual key from your data)
array_data = data["arr_0"]
pred_u_2 = array_data.item()["u_2"].ravel()

# Read the Gmsh-generated mesh in VTK format
reader = vtk.vtkDataSetReader()
reader.SetFileName(mesh_path)
reader.Update()
mesh = reader.GetOutput()

data_array = vtk.vtkDoubleArray()
data_array.SetName("PINN_T")
data_array.SetNumberOfComponents(1)
data_array.SetNumberOfTuples(mesh.GetNumberOfPoints())
for i, value in enumerate(pred_u_2):
    data_array.SetValue(i, value)
mesh.GetPointData().AddArray(data_array)

# Write the modified mesh with data to a VTK file
writer = vtk.vtkDataSetWriter()
writer.SetFileName(output_path)
writer.SetInputData(mesh)
writer.Write()
