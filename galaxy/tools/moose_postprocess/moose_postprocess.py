import pyvista as pv
# import matplotlib.pyplot as plt
import gc
import argparse
import tempfile
import os
import shutil

parser = argparse.ArgumentParser(
    description="Postprocess Moose simulation data for visualization in Omniverse."
)

parser.add_argument(
    "--simulation_time",
    type=float,
    required=True,
    help="Total simulation time in seconds."
)
parser.add_argument(
    "--interval_time",
    type=float,
    required=True,
    help="Time interval between simulation steps in seconds."
)
parser.add_argument(
    "--simulation_outputs",
    required=True,
    help="List of input files. These should be the output files from Moose simulation."
)

args = parser.parse_args()
extracted_outputs = []
with tempfile.TemporaryDirectory() as tmpdir:
    copied_files = []
    with open(args.simulation_outputs) as f:
        all_outputs = [line.strip() for line in f if line.strip()]

    for item in all_outputs:
        filepath, original_name, ext = item.split(" ", 2)

        if ext not in ["vtu", "pvtu"]:
            continue

        tmp_filepath = os.path.join(tmpdir, f"{original_name}.{ext}")
        shutil.copy(filepath, tmp_filepath)
        copied_files.append((original_name, ext, tmp_filepath))

    for original_name, ext, tmp_filepath in copied_files:
        if ext == "vtu":
            continue  
        mesh = pv.read(tmp_filepath)

        gc.collect()

        if 'temperature' not in mesh.point_data:
            print(f"Warning: 'temperature' not found in {original_name}.{ext}")
            continue
      
        temperature = mesh.point_data['temperature']
        extracted_outputs.append((original_name, temperature))

with open('output.csv', "w", newline="") as f:
    f.write("filename,temperature\n")
    for original_name, temperature in extracted_outputs:
        for t in temperature:
            f.write(f"{original_name},{t}\n")
