# Import necessary libraries
from abaqus import *
from abaqusConstants import *
from odbAccess import *
import numpy as np
import argparse

def write_vtk_file(vtk_file_path, node_labels, FEM_temperatures, element_labels, connectivity, instance):
    # Open the VTK file for writing
    with open(vtk_file_path, "w") as vtk_file:
        vtk_file.write("# vtk DataFile Version 2.0\n")
        vtk_file.write("Abaqus Temperature Field Data\n")
        vtk_file.write("ASCII\n")
        vtk_file.write("DATASET UNSTRUCTURED_GRID\n")

        # Write the node coordinates
        vtk_file.write("POINTS %d double\n" % len(node_labels))
        for node_label in node_labels:
            node = instance.nodes[node_label-1]  # node_label starts from 1, while Python list index starts from 0
            vtk_file.write("%f %f %f\n" % (node.coordinates[0], node.coordinates[1], node.coordinates[2]))

        # Write the element connectivity
        vtk_file.write("\nCELLS %d %d\n" % (len(element_labels), len(element_labels) * 9))
        for elem_connectivity in connectivity:
            vtk_file.write("%d %s\n" % (len(elem_connectivity), ' '.join(map(str, [node-1 for node in elem_connectivity]))))

        # Write the cell types (DC3D8: VTK_HEXAHEDRON = 12)
        vtk_file.write("\nCELL_TYPES %d\n" % len(element_labels))
        for _ in element_labels:
            vtk_file.write("12\n")

        # Write the temperature field data from FEM (Abqaqus ODB)
        vtk_file.write("\nPOINT_DATA %d\n" % len(node_labels))
        vtk_file.write("SCALARS FEM_T double 1\n")
        vtk_file.write("LOOKUP_TABLE default\n")
        for temperature in FEM_temperatures:
            vtk_file.write("%f\n" % temperature)

def read_temperature_field(odb_path, step_name, instance_name, temperature_field_name):
    # Open the ODB file
    odb = openOdb(odb_path)

    # Get the specified step and instance
    step = odb.steps[step_name]
    instance = odb.rootAssembly.instances[instance_name]

    # Get the temperature field output
    temperature_field = step.frames[-1].fieldOutputs[temperature_field_name]

    # Get the node labels and corresponding temperatures
    node_labels = []
    temperatures = []
    for node_temperature in temperature_field.values:
        node_labels.append(node_temperature.nodeLabel)
        temperatures.append(node_temperature.data)

    # Get the element connectivity
    element_labels = []
    connectivity = []
    for element in instance.elements:
        element_labels.append(element.label)
        connectivity.append(element.connectivity)

    # Close the ODB file
    odb.close()

    return node_labels, temperatures, element_labels, connectivity

def run(args):
    # Read temperature field data, element connectivity from the ODB file
    node_labels, FEM_temperatures, element_labels, connectivity = read_temperature_field(
        args.odb_file_path, args.step_name, args.instance_name, args.temperature_field_name
    )

    # Open the ODB file
    odb = openOdb(args.odb_file_path)

    # Get the specified instance
    instance = odb.rootAssembly.instances[args.instance_name]

    # Write external temperature data and element connectivity to a VTK file
    write_vtk_file(args.vtk_file_path, node_labels, FEM_temperatures, element_labels, connectivity, instance)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ODB to VTK converter")
    parser.add_argument('-i', '--odb_file_path', required=True, help="Path to input ODB file.")
    parser.add_argument('-s', '--step_name', default='Step-1', help="Name of the step in the ODB file.")
    parser.add_argument('-inst', '--instance_name', default='PV1', help="Name of the instance in the ODB file.")
    parser.add_argument('-f', '--temperature_field_name', default='NT11', help="Name of the temperature field in the ODB file.")
    parser.add_argument('-o', '--vtk_file_path', default='FE_res.vtk', help="Path to output VTK file.")
    parser.set_defaults(func=run)
    args = parser.parse_args()
    args.func(args)

    





