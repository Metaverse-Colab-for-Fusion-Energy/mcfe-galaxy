import FreeCAD
import Part
import Mesh

# import argparse

# parser = argparse.ArgumentParser(
#     description="stp to h5m geometry converter",
#     prog="stp_to_stl.py"
# )

# parser.add_argument("stp_to_convert", help="stp file to convert")

# args = parser.parse_args()
# stp_file = args.stp_to_convert

shape = Part.Shape()
shape.read('dagmc.stp')
doc = App.newDocument('Doc')
pf = doc.addObject("Part::Feature","MyShape")
pf.Shape = shape
Mesh.export([pf], 'dagmc.stl')