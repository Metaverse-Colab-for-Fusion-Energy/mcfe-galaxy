import argparse
import dagmc_h5m_file_inspector as di

#############
# IMPORT CAD
#############

parser = argparse.ArgumentParser(
    prog='h5m_materials.py',
    description = 'Returns a list of material volumes from the inputted h5m file. Usage: python h5m_materials.py <h5m CAD file> <output text file>'
)

parser.add_argument('h5m_CAD', help='dagmc.h5m CAD file to get the volume names from')
parser.add_argument('output_file', help='material_volume_list.txt file with to output the volume names for material assignment from the h5m CAD file')

args = parser.parse_args()

geometry_path = args.h5m_CAD
output_file = args.output_file

volumes = di.get_materials_from_h5m(geometry_path)

with open(output_file, 'w') as f:
    for volume in volumes:
        f.write(f"{volume}\n")