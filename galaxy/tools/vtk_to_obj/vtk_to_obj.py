#!/usr/bin/env python
import os
import pyvista as pv
import argparse
import pandas as pd


def convertFiles(input_file, field_name, obj_file_root, csv_file_root):
    # Prepare to store temperature data
    point_temperature_data = {}

    # Read the VTK file
    mesh = pv.read(input_file)
    print("Processing file:", input_file)

    # Extract the basename of the file without extension
    basename = os.path.splitext(os.path.basename(input_file))[0]

    # Check if the specified field exists
    if field_name not in mesh.point_data:
        print(f"No '{field_name}' scalar data found in {input_file}.")
        return

    # Determine if the file is a mesh or a point cloud
    if mesh.n_cells == 0:
        print(f"The file {input_file} is identified as a point cloud. Extracting all points' field data.")
        # Extract all points' field data
        point_temperature = mesh.point_data[field_name]
        point_temperature_data[basename] = point_temperature
    else:
        # Extract the surface of the mesh
        surface_mesh = mesh.extract_surface()
        print("Extracted surface mesh.")

        # Extract temperature data on the surface points
        surface_temperature = surface_mesh.point_data[field_name]
        point_temperature_data[basename] = surface_temperature

        # Optional: Convert the surface mesh to OBJ and save
        plotter = pv.Plotter(off_screen=True)
        _ = plotter.add_mesh(surface_mesh)
        plotter.export_obj(obj_file_root)
        plotter.close()
        print(f"OBJ file saved as: {obj_file_root}")

    # Save the point temperature data to a CSV file
    save_temperature_data(csv_file_root, point_temperature_data)


def save_temperature_data(csv_file_path, temperature_data):
    # Create a Pandas DataFrame from the temperature data
    temp_df = pd.DataFrame.from_dict(temperature_data, orient='index').transpose()

    # Save to CSV
    temp_df.to_csv(csv_file_path, index=False)
    print(f"Temperature data saved to {csv_file_path}")


def run(args):
    convertFiles(args.input_file, args.field_name, args.obj_file_root, args.csv_file_root)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="VTK to OBJ converter with surface or point cloud temperature extraction")
    parser.add_argument('-i', '--input_file', required=True, help="Path to input VTK file.")
    parser.add_argument('-n', '--field_name', required=True, help="Name of field in VTK file.")
    parser.add_argument('-objr', '--obj_file_root', default='output', help="Root name for OBJ output files.")
    parser.add_argument('-csvr', '--csv_file_root', default='output', help="Root name for CSV output files.")
    parser.set_defaults(func=run)
    args = parser.parse_args()
    args.func(args)
