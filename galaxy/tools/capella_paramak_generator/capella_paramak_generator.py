import paramak
import numpy as np
import argparse
from stl_to_h5m import stl_to_h5m
import json
import os

parser = argparse.ArgumentParser(
    prog="paramak_generator.py",
    description="""Paramak geometry generator.
        Usage: python paramak_generator.py <config_file>""",
)

parser.add_argument(
    "config_file",
    help="""Config .txt file with the parameters for the geometry creation.
    See:
        templates/JSON Generators/parametric_json_creator.py
    for more details.""",
)
args = parser.parse_args()
config_path = args.config_file


def parametric_blanket(geometry):
    """
    Function which creates a Blanket, firstwall, divertor and plasma region,
        and outputs a H5M file for OpenMC. ALso returns the plasma
        triangularity and elongation valves to be used when creating the
        plasma in OpenMC.

        Arguments:
            First_wall_thickness : The thickness of the Firstwall shield of
                the Tokamak(cm)
            Blanket_outboard_thickness: Thickness of the outboard blanket, The breeding zone
                equals Blanket_thickness - Blanket_Structure_Thicnkness (cm)
            Blanket_inboard_thickness: Thickness of the inboard blanket, The breeding zone
                equals Blanket_thickness - Blanket_Structure_Thicnkness (cm)
            Manifold_thickness: The Thickness of the Manifold to the rear of
                the blanket (cm)
            Plasma_offset: Distance between the firstwall and the plasma (cm)
            Blanket_structure_thickness: The thickness of the firstwall
                structure, between the firstwall shield plates and the
                breeding material
            Distance_between_segment: The toroidal gaps distance between each
                blanket unit (cm)
            Multiplier_thickness: Thickness of the Multiplier if not required
                it must be 0 (cm)
            Reflector_thickness: Thickness of the Reflector if not required
                it be 0 (cm)
            amount_of_segments_pol: The number of poloidal segments of the blanket
            amount_of_segments_tor: The number of toroidal segments of the blanket
            Minor_radius: The lenght of the plasma from the centre to the edge
                in a straight line on the x plane (cm)
            Major_radius: The lenght from the (0,0,0) coordinate to the centre
                of the plasma (cm)
            html_output: Creates an 3D html output to view the reactor created
    """
    # For testing
    Final_Blanket = []  # A list containing items for the final blanket
    
    try:
        First_wall_thickness = float(geometry["firstwall_thickness"])
        Blanket_outboard_thickness = float(geometry["blanket_outboard_thickness"])
        Blanket_inboard_thickness = float(geometry["blanket_inboard_thickness"])
        Manifold_thickness = float(geometry["manifold_thickness"])
        Plasma_offset = float(geometry["plasma_offset"])
        Blanket_structure_thickness = float(
            geometry["blanket_structure_thickness"]
        )
        Distance_between_segment = float(geometry["distance_between_segments"])
        Multiplier_thickness = float(geometry["multiplier_thickness"])
        Reflector_thickness = float(geometry["reflector_thickness"])
        amount_of_segments_pol = int(geometry["amount_of_segments_poloidal"])
        amount_of_segments_tor_in = int(geometry["amount_of_segments_toroidal_inboard"])
        amount_of_segments_tor_out = int(geometry["amount_of_segments_toroidal_outboard"])
        Minor_radius = float(geometry["minor_radius"])
        Major_Radius = float(geometry["major_radius"])
        # html_output = geometry["html_output"]
    except ValueError:
        print("Error: The input values much match the expected types")

    # Error Capture 50 represents the central solenoid 3603
    if float(Major_Radius) - 50 <= float(
        First_wall_thickness
        + Blanket_outboard_thickness
        + Manifold_thickness
        + Plasma_offset
        + Minor_radius
        + Blanket_structure_thickness
        + Multiplier_thickness
        + Reflector_thickness
    ):
        print(
            "Error: The Major Radius must be 50cm > all other inputs combined"
        )
        exit()

    # Error Capture for Blanket size
    if float(Blanket_outboard_thickness) <= float(
        Blanket_structure_thickness
        + Reflector_thickness
        + Multiplier_thickness
    ):
        print("Error: The Blanket unit must be larger than its parts")
        exit()

    # For error caused by zero input for reflector and multiplier
    cut_Structure_values = []  # A list of item that will cut the Structure
    cut_Blanket_value = []  # A list of items to cut the blanket
    cut_poloidal_values = [] ## A list of items to segment poloidally 

    # Create plasma and firstwall
    # Rotation angle fo the tokamak
    Angle = float(geometry['angle_end']) - float(geometry['angle_start'])
    gap = 2  # Gap between the in and out board blanket

    Plasma = paramak.Plasma(
        minor_radius=Minor_radius,
        major_radius=Major_Radius,
        # Must be outputted for the plasma parameters in neutronics
        triangularity=geometry['triangularity'],
        # Must be outputted for the plasma parameters in neutronics
        elongation=geometry['elongation'],
        rotation_angle=Angle,
    )

    ## Create cutting tools
    Structure_star_cutter_in = paramak.BlanketCutterStar(
        height=Major_Radius * 3,
        distance=Distance_between_segment,  # Distance between segments
        azimuth_placement_angle=np.linspace(
            0, 360, (amount_of_segments_tor_in), endpoint=False
        ),
    )
    # Used to cut the Blanket from the structure
    Blanket_star_cutter_in = paramak.BlanketCutterStar(
        height=Major_Radius * 3,
        distance=Distance_between_segment
        + (Blanket_structure_thickness * 2),  # Distance between segments
        azimuth_placement_angle=np.linspace(
            0, 360, (amount_of_segments_tor_in), endpoint=False
        ),
    )
    ## Create cutting tools
    Structure_star_cutter_out = paramak.BlanketCutterStar(
        height=Major_Radius * 3,
        distance=Distance_between_segment,  # Distance between segments
        azimuth_placement_angle=np.linspace(
            0, 360, (amount_of_segments_tor_out), endpoint=False
        ),
    )
    # Used to cut the Blanket from the structure
    Blanket_star_cutter_out = paramak.BlanketCutterStar(
        height=Major_Radius * 3,
        distance=Distance_between_segment
        + (Blanket_structure_thickness * 2),  # Distance between segments
        azimuth_placement_angle=np.linspace(
            0, 360, (amount_of_segments_tor_out), endpoint=False
        ),
    )

    # Blanket_cut Shape created to cut the remaining shapes for the divertor
    # Not used in the final reactor

    Blanket_cut = paramak.BlanketFP(
        plasma=Plasma,
        # To make it thicker than the Divertor for cutting
        thickness=Blanket_outboard_thickness + Plasma_offset + Manifold_thickness,
        stop_angle=230,
        start_angle=-60,
        # To make it thicker on the internal dimensions for cutting
        offset_from_plasma=Plasma_offset - First_wall_thickness,
        rotation_angle=Angle,
    )

    # Creates the gap between the inboard and outboard at the plasma high point
    inboard_to_outboard_gaps = paramak.RotateStraightShape(
        points=[
            (Plasma.high_point[0] - (0.5 * gap), Plasma.high_point[1]),
            (Plasma.high_point[0] - (0.5 * gap), Plasma.high_point[1] + 1000),
            (Plasma.high_point[0] + (0.5 * gap), Plasma.high_point[1] + 1000),
            (Plasma.high_point[0] + (0.5 * gap), Plasma.high_point[1]),
        ],
        rotation_angle=Angle,
    )

    # Create components

    # Test to check if the values for Multiplier and Reflector is zero
    if float(Reflector_thickness) > 0:
        Reflector_out = paramak.BlanketFP(
            plasma=Plasma,
            thickness=Reflector_thickness,
            stop_angle=90,
            start_angle=-60,
            offset_from_plasma=Plasma_offset
            + First_wall_thickness
            + Blanket_outboard_thickness
            - Reflector_thickness,
            rotation_angle=Angle,
            cut=[Blanket_star_cutter_out, inboard_to_outboard_gaps],
            color=list(
                np.random.rand(
                    3,
                )
            ),
            name="Reflector_outboard",
        )
        # Used just to cut a larger section
        Reflector_cut_out = paramak.BlanketFP(
            plasma=Plasma,
            thickness=Reflector_thickness + 5,
            stop_angle=90,
            start_angle=-60,
            offset_from_plasma=Plasma_offset
            + First_wall_thickness
            + Blanket_outboard_thickness
            - Reflector_thickness,
            rotation_angle=Angle,
            cut=[Blanket_star_cutter_out, inboard_to_outboard_gaps],
            color=list(
                np.random.rand(
                    3,
                )
            ),
            name="Reflector",
        )
        cut_Structure_values.append(Reflector_cut_out)
        cut_Blanket_value.append(Reflector_cut_out)
        cut_poloidal_values.append(Reflector_out)

        Reflector_in = paramak.BlanketFP(
            plasma=Plasma,
            thickness=Reflector_thickness,
            stop_angle= 230,
            start_angle=90,
            offset_from_plasma= Plasma_offset 
            + First_wall_thickness 
            + Blanket_inboard_thickness 
            - Reflector_thickness,
            rotation_angle=Angle,
            cut = [Blanket_star_cutter_in, inboard_to_outboard_gaps],
            color= list(np.random.rand(3,)),
            name = 'Reflector_inboard'
        )
        ##Used just to cut a larger section
        Reflector_cut_in = paramak.BlanketFP(
            plasma=Plasma,
            thickness=Reflector_thickness +5,
            stop_angle= 230,
            start_angle=90,
            offset_from_plasma= Plasma_offset 
            + First_wall_thickness 
            + Blanket_inboard_thickness 
            - Reflector_thickness,
            rotation_angle=Angle,
            cut = [Blanket_star_cutter_in, inboard_to_outboard_gaps],
            color= list(np.random.rand(3,)),
            name = 'Reflector'
        )
        cut_Structure_values.append(Reflector_cut_in)
        cut_Blanket_value.append(Reflector_cut_in)
        cut_poloidal_values.append(Reflector_in)

    if float(Multiplier_thickness) > 0:
        Multiplier_in = paramak.BlanketFP(
            plasma=Plasma,
            thickness=Multiplier_thickness,
            stop_angle=230,
            start_angle=90,
            offset_from_plasma=Plasma_offset
            + First_wall_thickness
            + Blanket_structure_thickness,
            rotation_angle=Angle,
            cut=[Blanket_star_cutter_in, inboard_to_outboard_gaps],
            color=list(
                np.random.rand(
                    3,
                )
            ),
            name="Multiplier_inboard",
        )
        cut_Structure_values.append(Multiplier_in)
        cut_poloidal_values.append(Multiplier_in)
        cut_Blanket_value.append(Multiplier_in)

        Multiplier_out = paramak.BlanketFP(
            plasma=Plasma,
            thickness=Multiplier_thickness,
            stop_angle=90,
            start_angle=-60,
            offset_from_plasma=Plasma_offset
            + First_wall_thickness
            + Blanket_structure_thickness,
            rotation_angle=Angle,
            cut=[Blanket_star_cutter_out, inboard_to_outboard_gaps],
            color=list(
                np.random.rand(
                    3,
                )
            ),
            name="Multiplier_outboard",
        )
        cut_Structure_values.append(Multiplier_out)
        cut_poloidal_values.append(Multiplier_out)
        cut_Blanket_value.append(Multiplier_out)

    Firstwall_in = paramak.BlanketFP(
        plasma=Plasma,
        thickness=First_wall_thickness,
        stop_angle=230,
        start_angle=90,
        offset_from_plasma=Plasma_offset,
        rotation_angle=Angle,
        num_points=100,
        cut=[Blanket_star_cutter_in],
        color=list(
            np.random.rand(
                3,
            )
        ),
        name="Firstwall_inboard",
    )
    Final_Blanket.append(Firstwall_in)

    Firstwall_out = paramak.BlanketFP(
        plasma=Plasma,
        thickness=First_wall_thickness,
        stop_angle=90,
        start_angle=-60,
        offset_from_plasma=Plasma_offset,
        rotation_angle=Angle,
        num_points=100,
        cut=[Blanket_star_cutter_out],
        color=list(
            np.random.rand(
                3,
            )
        ),
        name="Firstwall_outboard",
    )
    Final_Blanket.append(Firstwall_out)

    Manifold_out = paramak.BlanketFP(
        plasma =Plasma,
        thickness = Manifold_thickness,
        stop_angle= 90,
        start_angle=-60,
        offset_from_plasma= Plasma_offset 
        + First_wall_thickness 
        + Blanket_outboard_thickness,
        rotation_angle=Angle,
        cut = [inboard_to_outboard_gaps],
        name = 'Manifold_outboard'
    )
    Final_Blanket.append(Manifold_out)

    Manifold_in = paramak.BlanketFP(
        plasma =Plasma,
        thickness = Manifold_thickness + 
        (Blanket_outboard_thickness - Blanket_inboard_thickness),
        stop_angle= 230,
        start_angle= 90,
        offset_from_plasma= Plasma_offset 
        + First_wall_thickness 
        + Blanket_inboard_thickness,
        rotation_angle=Angle,
        cut = [inboard_to_outboard_gaps],
        name = 'Manifold_inboard'
    )
    Final_Blanket.append(Manifold_in)

    Blanket_out = paramak.BlanketFP(
        plasma=Plasma,
        thickness=Blanket_outboard_thickness 
        - Blanket_structure_thickness,
        stop_angle= 90,
        start_angle= -60,
        offset_from_plasma=Plasma_offset
        + First_wall_thickness
        + Blanket_structure_thickness,
        rotation_angle=Angle,
        cut=[Blanket_star_cutter_out, inboard_to_outboard_gaps]
        + cut_Blanket_value,
        color=list(
            np.random.rand(
                3,
            )
        ),
        name="Blanket_outboard",
    )
    cut_poloidal_values.append(Blanket_out)

    Blanket_in = paramak.BlanketFP(
        plasma=Plasma,
        thickness=Blanket_inboard_thickness -  Blanket_structure_thickness,
        stop_angle= 230,
        start_angle=90,
        offset_from_plasma= Plasma_offset 
        + First_wall_thickness 
        + Blanket_structure_thickness,
        rotation_angle=Angle,
        cut = [Blanket_star_cutter_in, inboard_to_outboard_gaps] 
        + cut_Blanket_value,
        color= list(np.random.rand(3,)),
        name = 'Blanket_inboard'
    )
    cut_poloidal_values.append(Blanket_in)

    Blanket_cut_Structure_out = paramak.BlanketFP(
        plasma=Plasma,
        thickness=Blanket_outboard_thickness
        + Blanket_structure_thickness
        + Reflector_thickness,
        stop_angle=90,
        start_angle=-60,
        offset_from_plasma=Plasma_offset
        + First_wall_thickness
        + Blanket_structure_thickness,
        rotation_angle=Angle,
        cut=[Blanket_star_cutter_out, inboard_to_outboard_gaps]
        + cut_Blanket_value,
        color=list(
            np.random.rand(
                3,
            )
        ),
    )
    Blanket_cut_Structure_in = paramak.BlanketFP(
        plasma=Plasma,
        thickness=Blanket_outboard_thickness
        + Blanket_structure_thickness
        + Reflector_thickness,
        stop_angle=230,
        start_angle=90,
        offset_from_plasma=Plasma_offset
        + First_wall_thickness
        + Blanket_structure_thickness,
        rotation_angle=Angle,
        cut=[Blanket_star_cutter_in, inboard_to_outboard_gaps]
        + cut_Blanket_value,
        color=list(
            np.random.rand(
                3,
            )
        ),
    )
    outboard_Structure_Blanket = paramak.BlanketFP(
        plasma=Plasma,
        thickness=Blanket_outboard_thickness,
        stop_angle=90,
        start_angle=-60,
        offset_from_plasma= Plasma_offset 
        + First_wall_thickness,
        rotation_angle=Angle,
        cut=[Blanket_cut_Structure_out, Structure_star_cutter_out, inboard_to_outboard_gaps] 
        + cut_Structure_values,
        color=list(
            np.random.rand(
                3,
            )
        ),
        name="Outboard_Structure_Blanket",
    )
    cut_poloidal_values.append(outboard_Structure_Blanket)

    inboard_Structure_Blanket = paramak.BlanketFP(
        plasma=Plasma,
        thickness=Blanket_inboard_thickness,
        stop_angle=230,
        start_angle=90,
        offset_from_plasma=Plasma_offset 
        + First_wall_thickness,
        rotation_angle=Angle,
        cut=[Blanket_cut_Structure_in, Structure_star_cutter_in, inboard_to_outboard_gaps]
        + cut_Structure_values,
        color=list(
            np.random.rand(
                3,
            )
        ),
        name="Inboard_Structure_Blanket",
    )
    Final_Blanket.append(inboard_Structure_Blanket)
    print(inboard_Structure_Blanket.name)
    Divertor = paramak.BlanketFP(
        plasma=Plasma,
        thickness=Blanket_outboard_thickness + Manifold_thickness,
        stop_angle=270,
        start_angle=-90,
        offset_from_plasma=Plasma_offset + First_wall_thickness,
        rotation_angle=Angle,
        cut=Blanket_cut,
        color=list(
            np.random.rand(
                3,
            )
        ),
        name="Divertor",
    )
    Final_Blanket.append(Divertor)

    ## Used to gather all shapes that need cutting poloially and cut to the amount of 
    for component in cut_poloidal_values:
        
        segmented_structure = paramak.PoloidalSegments(
            shape_to_segment=component,
            center_point=(Major_Radius, 0),  # this is the middle of the plasma
            number_of_segments=amount_of_segments_pol,
            color= list(np.random.rand(3,)),
            name = component.name
        )
        Final_Blanket.append(segmented_structure)

    shape_name = []
    #reactor = paramak.Reactor(Final_Blanket)
    #reactor.export_html_3d('example.html')
    
    
    # Create stl files
    for shape in Final_Blanket:
        shape.export_stl(str(shape.name) + ".stl")
        shape_name.append((str(shape.name) + ".stl", str(shape.name)))

    stl_to_h5m(
        files_with_tags=shape_name,
        h5m_filename="dagmc.h5m",
    )

    os.system("rm *.stl")
    

if __name__ == "__main__":
    with open(config_path, "r") as config_file:
        config_dict = json.load(config_file)

    parametric_blanket(config_dict["geometry"])
