# pylint: disable=import-error
"""
This module contains functionality for calculating the bounding box of a 3D object
imported from a STEP file using the FreeCAD library.

The module uses the FreeCAD and Part libraries to load the STEP file and access the
3D object. It then calculates the bounding box of the object and writes the dimensions
to a specified output file. The dimensions are rounded to 5 decimal places for precision.

The module also includes functionality for parsing command-line arguments to specify
the output file path.

Dependencies:
    argparse: A standard library module for parsing command-line arguments.
    FreeCAD: A Python library for scripting FreeCAD, a 3D CAD modeler.
    Part: A FreeCAD module for working with 3D parts.
"""

import argparse
import FreeCAD
import Part


# Load the STEP file
doc = FreeCAD.newDocument()
Part.insert("file_to_import.step", doc.Name)

# Get the active object (assuming the STEP file has one main object)
obj = doc.ActiveObject

# Calculate the bounding box
bbox = obj.Shape.BoundBox

parser = argparse.ArgumentParser()
parser.add_argument('output_file_path')
args = parser.parse_args()
output_file = "output.csv"

# Write the bounding box dimensions to a file, rounding to 5 decimal places
with open(output_file, "w", encoding='utf-8') as file:
    file.write("Min/Max,X,Y,Z\n")

    # Write the data with rounding
    file.write(
        f"Min,{round(bbox.XMin, 5)},{round(bbox.YMin, 5)},{round(bbox.ZMin, 5)}\n")
    file.write(
        f"Max,{round(bbox.XMax, 5)},{round(bbox.YMax, 5)},{round(bbox.ZMax, 5)}\n")

FreeCAD.closeDocument(doc.Name)
