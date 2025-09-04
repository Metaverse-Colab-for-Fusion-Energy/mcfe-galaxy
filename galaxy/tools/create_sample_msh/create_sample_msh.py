import gmsh
import argparse

parser = argparse.ArgumentParser(
    prog="create_sample_msh.py",
    description="Usage: python heatflux-to-PINN.py <input.vtk> <input.txt> <output.txt>",
)

parser.add_argument(
    "sample_diameter", help="diameter of the sample cylinder in mm", type=float
)
parser.add_argument(
    "sample_thickness", help="thickness of the sample cylinder in mm", type=float
)
args = parser.parse_args()

sample_diameter = float(args.sample_diameter)
sample_thickness = float(args.sample_thickness)

gmsh.initialize()
gmsh.model.add("test")

circle = gmsh.model.occ.addDisk(0, 0, 0, sample_diameter/2, sample_diameter/2)
gmsh.model.occ.synchronize()

ext = gmsh.model.occ.extrude([(2, circle)], 0, 0, sample_thickness)
gmsh.model.occ.synchronize()

surfaces = gmsh.model.getEntities(dim=2)

bottom_tag = gmsh.model.addPhysicalGroup(2, [3])
gmsh.model.setPhysicalName(2, bottom_tag, "left")

top_tag = gmsh.model.addPhysicalGroup(2, [1])
gmsh.model.setPhysicalName(2, top_tag, "right")

side_tag = gmsh.model.addPhysicalGroup(2, [2])
gmsh.model.setPhysicalName(2, side_tag, "side") 

vol_tag = gmsh.model.addPhysicalGroup(3, [1])
gmsh.model.setPhysicalName(3, vol_tag, "volume")

# gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 0.5)
# gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 0.5)
gmsh.model.mesh.generate(3)
node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
num_nodes = len(node_tags)
with open("num_nodes.txt", "w") as f:
    f.write(f"{num_nodes}\n")

gmsh.write("mesh.msh")
# gmsh.fltk.run()  
gmsh.finalize()
