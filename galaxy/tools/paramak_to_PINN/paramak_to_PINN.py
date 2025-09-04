import FreeCAD
import Part

step_file_path = "input.stp"

# Load the STEP file
doc = FreeCAD.newDocument("MyDocument")
Part.insert(step_file_path, doc.Name)
shape = doc.Objects[0].Shape

# iterate over every object - idea is that there is only one object in the active document that is a paramak geom with a hidden face
for selected_object in FreeCAD.ActiveDocument.Objects:
    if str(selected_object) == "[<App::Origin object>]":
        print(
            "[ERROR] Origin object selected. Select a valid mesh, part, or body object."
        )
    #    return None
    if str(selected_object) == "<Part::PartFeature>":
        # Access the selected object
        print("Selected object:", selected_object.Name)
        shp = selected_object.Shape
        volumes_list = []
        match_check = None
        match_list = []
        if len(shp.Faces) > 1:
            face = shp.Faces
            shell_outer_sur = Part.makeShell([face[3]])
            shell_outer_sur.exportStl("outer.stl")

            shell_side_sur = Part.makeShell([face[1], face[5]])
            shell_side_sur.exportStl("side.stl")

            shell_inner_sur = Part.makeShell([face[0]])
            shell_inner_sur.exportStl("inner.stl")

            # now take the list of hidden faces and get the list of real faces
            final_face_list = []
            for face_idx, face in enumerate(shp.Faces):
                if face_idx not in match_list:
                    final_face_list.append(face)
            # finally, make the shape and show the part
            shell = Part.makeShell(final_face_list)
            Part.show(shell)
            FreeCAD.ActiveDocument.recompute()
            shp.exportStl("vessel.stl")

        else:
            print("Find Faulty face")
    else:
        pass
