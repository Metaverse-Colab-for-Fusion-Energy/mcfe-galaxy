import argparse
from modulus.sym.geometry.tessellation import Tessellation
from modulus.sym.geometry import Geometry

parser = argparse.ArgumentParser(
    prog="heatflux-to-PINN.py",
    description="Usage: python heatflux-to-PINN.py -n <nr_points>",
)
parser.add_argument(
    "-n", "--nr_points", help="number of points to sample", type=int
)

args = parser.parse_args()

number_of_points = args.nr_points

reactorwall = Tessellation.from_stl("Output_Vessel.stl", airtight=True)

# interior
sample_point = reactorwall.sample_interior(
    nr_points=number_of_points,
    compute_sdf_derivatives=False
)

data_tuples = list(zip(
    sample_point['x'],
    sample_point['y'],
    sample_point['z'],
    sample_point['area']
))
print(data_tuples)

file_path = 'test.txt'
with open(file_path, 'w') as file:
    for data_tuple in data_tuples:
        data_values = [str(value.item()) for value in data_tuple]
        tuple_string = ' '.join(data_values)
        file.write(tuple_string + '\n')
