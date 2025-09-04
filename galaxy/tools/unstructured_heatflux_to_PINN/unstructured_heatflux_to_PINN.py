import time
import multiprocessing

# import logging # Removing due to Galaxy incompatibility (makes tools fail)

import numpy as np
import vtk

import argparse

# from progressbar import progressbar

parser = argparse.ArgumentParser(
    prog="heatflux-to-PINN.py",
    description="Usage: python unstructured_heatflux_to_PINN.py <input.vtk> <input.txt> <output.txt>",
)

parser.add_argument(
    "input_vtk", help="vtk file with the heat flux (output from OpenMC)"
)
parser.add_argument(
    "input_txt", help="list of points to sample from (cleaned first so just x y z)"
)
parser.add_argument("output_txt", help="list of heating at sample points")

args = parser.parse_args()

input_vtk_path = args.input_vtk
input_txt_path = args.input_txt
output_path = args.output_txt

# logging.basicConfig(level=logging.INFO)

start_time = time.time()
print("Startup - setting start time")

# ------------------------------------------------------------------------------
# Global constants

UNITS_FACTOR = 100

# ------------------------------------------------------------------------------
# Set paths

# INPUT_PATH = "CSF_VTK_sample_data"
INPUT_COORDINATES = input_txt_path  # f"{INPUT_PATH}/input_coords.txt"
INPUT_VTK = input_vtk_path  # f"{INPUT_PATH}/output.vtk"

OUTPUT_FILENAME = output_path  # "heat_flux_output_PINN_2.txt"

print(f"Input coordinates file: {INPUT_COORDINATES}")
print(f"Input VTK file: {INPUT_VTK}")

# ------------------------------------------------------------------------------
# Load VTK file and create grid

print("Creating reader...")
reader = vtk.vtkUnstructuredGridReader()
reader.SetFileName(INPUT_VTK)
reader.Update()
print("Reader created!")

grid = reader.GetOutput()

# ------------------------------------------------------------------------------
# Create the VTK cell locator

print("Creating cell locator...")
cell_locator = vtk.vtkCellLocator()
cell_locator.SetDataSet(grid)
cell_locator.BuildLocator()
print("Cell locator created!")

# ------------------------------------------------------------------------------
# Define the search function


def vtkSearchPoints(aim_coor):
    # TODO: Make better (may be a gmsh problem)
    # Basically some values were too small and just out of range
    # so set slightly out of range values to 0
    # for id, value in enumerate(aim_coor):
    #     if value < 1e-5 and value > -1e-5:
    #         aim_coor[id] = 0.0
    #         print(aim_coor)
    cell_id = cell_locator.FindCell(aim_coor)

    # Check if a cell was found
    # TODO: make better - finding some values (~20 in 18,000,000) that are out
    # of range so here just return that the heat flux at these are 0 - need to
    # properly figure out why...
    if cell_id < 0:
        return 0
        # print(cell_id)
        # print(aim_coor)
        # raise Exception("Error: no data near this location")

    # Print the found cell ID
    cell_data = grid.GetCellData()
    cell_array = cell_data.GetArray(0)
    cell_value = cell_array.GetValue(cell_id)
    return cell_value


# ------------------------------------------------------------------------------
# Define the main function

if __name__ == "__main__":
    # --------------------------------------------------------------------------
    # Create output containers

    print("Reading coordinates file")
    coordinates = np.genfromtxt(INPUT_COORDINATES)

    # If coordinates has 4 columns, remove the last one and save it
    area = None
    if coordinates.shape[1] == 4:
        print("Coordinates file has 4 columns, removing the last one")
        area = coordinates[:, -1]
        coordinates = coordinates[:, :-1]
    # coordinates_raw = np.genfromtxt(INPUT_COORDINATES) / UNITS_FACTOR
    # coordinates = coordinates_raw * UNITS_FACTOR

    # --------------------------------------------------------------------------
    # Create a multiprocessing Pool

    print("Creating multiprocessing pool")
    pool = multiprocessing.Pool()

    # --------------------------------------------------------------------------
    # Use the pool to process the coordinates in parallel

    print("Begin processing")
    results = np.empty(coordinates.shape[0])
    input_map = pool.map(vtkSearchPoints, coordinates)
    for ii, result in enumerate(input_map):  # enumerate(progressbar(input_map)):
        results[ii] = result
    print("Processing finished")

    # --------------------------------------------------------------------------
    # Write output and cleanup

    print("Creating output file...")
    if area is None:
        out_array = np.column_stack([coordinates, results[:, None]])
    else:
        out_array = np.column_stack([coordinates, results[:, None], area[:, None]])
    np.savetxt(OUTPUT_FILENAME, out_array)
    print("Output file created")

    # Calculate the elapsed time
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time}")

    # Close the pool
    pool.close()
    pool.join()
