# pylint: disable=import-error
"""
This module contains the Torus class which is used to generate a 3D model of a torus-shaped tokamak. 

The Torus class extends the Workplane class from the CadQuery library. 
It uses various geometric parameters to define the 
shape of the torus and can generate 
either a solid model or a wireframe based on these parameters.

This module also includes the tf_step function from the tf_step_v3 module, 
which is used to create a toroidal field coil assembly.

The module uses constants to represent full and half revolve for better code readability.

Dependencies:
- csv: for reading data from CSV files
- os: for handling file and directory paths
- itertools: for advanced iteration tools like accumulate
- typing: for type hints
- cadquery: for 3D modeling
- numpy: for numerical operations
- paramak: for parametric 3D modeling in nuclear fusion research
- pylab: for scientific and technical computing
- tf_step_V3: for creating a toroidal field coil assembly
"""
import csv
import os
from itertools import accumulate
from typing import Iterable, Tuple

import cadquery as cq
import numpy as np
import paramak
from pylab import *
from tf_step_v3 import tf_step
# Defining constants for magic numbers
FULL_REVOLVE = 360
HALF_REVOLVE = 180


class Torus(cq.Workplane):
    """
    Class for creating a torus using CadQuery.

    Parameters:
        r_0 : float : Major radius ∏of the torus. Default is 2.2.
        aspect_ratio : float : Aspect Ratio. Default is 1.7.
        a : float : Minor radius of the torus.
        delta, si, sj, kappa, po : Various geometric parameters.
        degrees : int : Degrees to revolve. Default is 180.
        wire : bool : Whether to create a wireframe. Default is False.
        revolve_num : int : Number of revolves. Default is 1.
    """

    def __init__(
        self,
        r_0: float = 2.2,
        aspect_ratio: float = 1.7,
        a: float = None,
        delta: float = 1.0,
        si: float = 0.0,
        sj: float = 0.0,
        kappa: float = 2.0,
        po: int = 54,
        degrees: int = 180,
        wire: bool = False,
        revolve_num: int = 1,
    ):
        self.r_0 = r_0 if r_0 is not None else aspect_ratio * a
        self.aspect_ratio = aspect_ratio
        self.a = a if a is not None else r_0 / aspect_ratio
        self.delta = delta
        self.si = si
        self.sj = sj
        self.kappa = kappa
        self.po = po
        self.degrees = degrees
        self.wire = wire
        self.revolve_num = revolve_num
        self.construct_torus()

    def calculate_r(self, i: int) -> float:
        """
        Calculate the R-coordinate for a given index i.

        Parameters:
            i : int : Index in the loop to generate R and Z points.
        Returns:
            float : Calculated R value.
        """

        return self.r_0 + self.a * np.cos(
            np.pi
            + (i * np.pi / self.po)
            + (self.a * np.sin(self.delta)) *
            np.sin(np.pi + (i * np.pi / self.po))
        )

    def calculate_z(self, i: int, squaredness: float) -> float:
        """
        Calculate the Z-coordinate for a given index i.

        Parameters:
            i : int : Index in the loop to generate R and Z points.
            squaredness : float : Parameter to adjust the "squareness" of the torus.
        Returns:
            float : Calculated Z value.
        """

        return (
            self.a
            * self.kappa
            * np.sin(
                np.pi
                + (i * np.pi / self.po)
                + squaredness * np.sin(np.pi + (2 * i * np.pi / self.po))
            )
        )

    def get_r_and_z_points(self) -> Tuple[list, list]:
        """
        Generate the R and Z points to construct the torus.

        Returns:
            Tuple[list, list] : Lists of R and Z points.
        """

        r_points = []
        z_points = []

        for i in range(1, (2 * self.po)):
            r_val = self.calculate_r(i)
            z_val = self.calculate_z(i, self.si if i <= self.po else self.sj)

            r_points.append(np.round(r_val, 5))
            z_points.append(np.round(z_val, 5))

        return r_points, z_points

    def construct_torus(self):
        """
        Construct the torus using CadQuery. The constructed torus is stored in self.torus.
        """

        r_points, z_points = self.get_r_and_z_points()
        points = [[r, z] for r, z in zip(r_points, z_points)]

        radial_build_wire = cq.Workplane("XY").polyline(points).close()

        if not self.wire:
            self.torus = radial_build_wire.revolve(
                self.degrees, (0, -10, 0), (0, 10, 0)
            )

        else:
            self.torus = radial_build_wire


def write_csv(
    r_points,
    z_points,
    file_name="vessel_points.csv",
):
    """
    Writes the provided R and Z points to a CSV file.

    Parameters:
    R_points (list): The list of R points.
    Z_points (list): The list of Z points.
    file_name (str): The name of the CSV file to write to. Default is "vessel_points.csv".

    Returns:
    file_name (str): The name of the CSV file that was written to.
    """
    # Write the header and data
    with open(file_name, "w", encoding='utf-8', newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["X", "Y"])
        for r, z in zip(r_points, z_points):
            csv_writer.writerow([r, z])

    return file_name


def delete_csv_files(file_paths):
    """
    Deletes the CSV files at the provided file paths.

    Parameters:
    file_paths (list): The list of file paths to the CSV files to be deleted.

    Returns:
    None
    """
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")  # Just to confirm it's done


def find_coil_centrepoint(
    vessel_height,
    vessel_radius,
    tf,
    x_offset=0.25,
    inner_coil=True,
    top=True,
):
    """
    Function to find the centrepoint of the coils to use the paramak PF coil generation script

    Returns:
        Tuple[float, float]: X, Y coordinates for the centrepoint of coil
    """
    # Using ternary operator for compactness
    vertical_offset = 0.0 if top else -0.0

    coil_height = vessel_height + vertical_offset

    # Calculate horizontal offset based on whether it's an inner or outer coil
    # Calculate coil radius based on whether it's an inner or outer coil
    coil_radius = x_offset if inner_coil else x_offset
    # Apply horizontal offset to the coil radius

    print("PF COIL RADIUS: ", coil_radius)

    # Shift to ensure no overlap with TF coils

    if inner_coil:
        if coil_radius <= 0.0:
            print("COIL TOO SMALL")

    # Shift vertically if coils sit above/below TF coils
    # TF_dr = 0.4

    # Elongation = 2 so double radii
    if coil_height <= (-2) * (vessel_radius + tf):
        coil_height = coil_height - (2 * tf)
    elif coil_height >= (2) * (vessel_radius + tf):
        coil_height = coil_height + (2 * tf)

    return coil_radius, coil_height


def generate_pf_coil_set(
    heights,
    x_offsets,
    vessel_radius,
    tf_dr,
    pf_dr,
    pf_dz,
    major_radius,
    inner_coil=False,
    top=True,
    pf_coil_path=None
):
    """
    Generates a set of Poloidal Field (PF) coils for a fusion reactor and returns cadquery objects.

    The function uses paramak to create PF coil geometries which are then exported to STEP files.
    These files are imported as cadquery objects and returned in a list, with cleanup of the
    STEP files performed afterwards.

    Parameters:
    - heights (list of float): Vertical positions for the coil centers.
    - x_offsets (list of float): Radial offsets for the coil centers from the vessel's major radius.
    - vessel_radius (float): Radius of the vessel.
    - major_radius (float): Major radius of the tokamak.
    - inner_coil (bool): Specifies if the coils are inner (True) or outer (False).
    - top (bool): Specifies if the coils are on the top (True) or bottom (False) of the vessel.

    Returns:
    - list of cadquery.Workplane: Cadquery objects representing the PF coils.
    """
    # COIL PARAMETERS (hardcoded for now)
    r_turns = 10
    z_turns = 10
    current_per_turn = 2

    # HEIGHT = 0.2
    # WIDTH = 0.2
    # Prepare lists for cadquery objects and STEP file paths
    cq_coils, step_files = [], []

    # Create PF coil objects and corresponding STEP files
    for count, height in enumerate(heights):
        centerpoint = find_coil_centrepoint(
            height,
            vessel_radius,
            tf_dr,
            x_offsets[count],
            inner_coil,
            top,
        )
        print(count)
        print(x_offsets[count])
        print("CENTER POINT")
        print(centerpoint, centerpoint[0])
        print("COIl NUM = ", count)
        print("COIL PROPERTIES:")
        height = pf_dz
        print(height, pf_dr, pf_dz)
        print(height, vessel_radius, major_radius,
              x_offsets[count], inner_coil, top)
        pf_coil = paramak.PoloidalFieldCoil(
            height=pf_dz, width=pf_dr, center_point=centerpoint, workplane="XY"
        )
        print(centerpoint)
        step_filename = f"pf_coil_{count}.step"
        pf_coil.export_stp(step_filename)
        step_files.append(step_filename)

    # Import the STEP files into cadquery objects and remove the files
    for step_file in step_files:
        cq_coils.append(cq.importers.importStep(step_file))
        os.remove(step_file)

        # After all coils are generated and before the function returns, add this:
    coil_data = []
    for count, height in enumerate(heights):
        centerpoint = find_coil_centrepoint(
            height,
            vessel_radius,
            tf_dr,
            x_offsets[count],
            inner_coil,
            top,
        )

        coil_x = 0
        coil_y = centerpoint[1]
        coil_z = 0
        coil_data.append(
            [
                r_turns,
                z_turns,
                current_per_turn,
                centerpoint[0],
                pf_dr,
                pf_dz,
                coil_x,
                coil_y,
                coil_z,
                0,
                1,
                0,
            ]
        )

    # Write coil data to CSV
    write_pf_coils_to_csv(coil_data, pf_coil_path)

    return cq_coils


def generate_solenoid(
    solenoid_length, number_of_turns, loop_radius, solenoid_thickness
):
    """
    Generates a 3D CAD model of a solenoid with specified parameters.

    This function creates the solenoid by using paramak to create individual coils of the 
    solenoid and cadquery (cq) for further CAD manipulations.

    Parameters:
    - solenoid_length (float): The total length of the solenoid.
    - number_of_turns (int): The number of turns or coils in the solenoid.
    - loop_radius (float): The radius of each loop or coil in the solenoid.
    - solenoid_thickness (float): The thickness of the solenoid coils.

    The function calculates the position of each coil based on the solenoid length and number of 
    turns. Each coil is modeled with a fixed height and specified width (thickness), centered at 
    calculated positions along the solenoid's length. These coils are then exported as STEP files, a 
    common format in CAD software, for further processing or manipulation.

    Returns:
    - cad_coils (list): A list of cadquery objects representing each coil.

    Note:
    The STEP files generated during the process are deleted after being imported into cadquery.
    """
    # Initialize lists to store solenoid coils and filenames of the STEP files for CAD.
    sol_coils = []
    stp_files = []  # To store filenames of the STEP files
    cad_coils = []

    # Calculate the distance between each turn of the solenoid.
    dz = solenoid_length / number_of_turns
    # Calculate the starting height of the solenoid.
    start_height = -solenoid_length / 2

    # Loop over the number of turns to create each solenoid coil.
    for i in range(number_of_turns):
        # Calculate the height position for each coil.
        height = start_height + i * dz

        # Create a solenoid coil using paramak with specified dimensions and position.
        solenoid_coil = paramak.PoloidalFieldCoil(
            height=0.2,  # Fixed height of the coil
            width=solenoid_thickness,  # Thickness of the coil
            center_point=(loop_radius, height),  # Center position of the coil
            workplane="XY",  # Workplane for the coil
        )
        # Append the created coil to the sol_coils list.
        sol_coils.append(solenoid_coil)

        # Export the coil to a STEP file for CAD and store the filename.
        step_filename = f"solenoid_coil_{height}.step"
        solenoid_coil.export_stp(step_filename)
        stp_files.append(step_filename)

    # Import the exported STEP files for further CAD manipulation.
    for step_file in stp_files:
        # Import each STEP file and append to the cad_coils list.
        cad_coils.append(cq.importers.importStep(step_file))
        # Remove the STEP file after import to clean up.
        os.remove(step_file)

    # Return the list of CAD coil objects.
    return cad_coils


# Function to write or append coil data to a CSV file
def write_pf_coils_to_csv(coil_data, csv_file_path="pf_coils_1.csv"):
    """
    Writes or appends poloidal field (PF) coil data to a CSV file.

    Parameters:
    coil_data (list): The list of PF coil data to write to the CSV file.
    csv_file_path (str): The path to the CSV file to write to. Default is "pf_coils_1.csv".

    Returns:
    None
    """
    with open(csv_file_path, "a", newline="", encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerows(coil_data)
    print(f"PF Coil data appended to {csv_file_path}")


def run_code(
    accumulated_radii: Iterable[float],
    component_names: Iterable[str],
    aspect_ratio,
    tf_dz,
    tf_dr,
    pf_dz,
    pf_dr,
    sol,
    tf_coil_path,
    pf_coil_path
):
    """
    Runs the code to generate a tokamak assembly with specified component radii and names.

    This function takes an iterable of radii and an iterable of component names to construct a 
    3D model of a tokamak reactor. It calculates the major radius, creates plasma and 
    toroidal components, computes torus dimensions, generates TF coils, and positions 
    these coils to minimize interference with the reactor structure. 
    The final output is an assembly of the tokamak and its components.

    Parameters:
    - accumulated_radii (Iterable[float]): An iterable of floats representing the accumulated radii
      of the tokamak components.
    - component_names (Iterable[str]): An iterable of strings representing the names of the tokamak
      components.

    Returns:
    - tokamak_assembly (cq.Assembly): An assembly of the tokamak and all its components.
    - coils (cq.Assembly): An assembly of the coils used in the tokamak.
    - reactor_only (cq.Assembly): The tokamak assembly excluding the coils.
    """
    vessel_height = 0

    reactor_components, vessel_r_points, vessel_z_points = [], [], []
    tokamak_assembly, coils, reactor_only = cq.Assembly(), cq.Assembly(), cq.Assembly()

    # Accumulate and round off radii for precision
    accumulated_radii = list(accumulate(accumulated_radii))
    accumulated_radii = [round(x, 2) for x in accumulated_radii]

    # Flag to identify the plasma component
    is_plasma = True

    # Calculate the major radius based on aspect ratio and maximum of accumulated radii
    # aspect_ratio = 2.2  # Aspect ratio for tokamak design
    major_radius = aspect_ratio * (accumulated_radii[0])
    print("PLASMA MINOR RAD : ", accumulated_radii[0])
    print("MAJOR RAD : ", major_radius)
    print("ASPECT RATIO : ", aspect_ratio)

    # Iterate over component radii and names to create toroidal components
    for minor_radius, component_name in zip(accumulated_radii, component_names):
        # Create a plasma torus for the first component
        print("Minor radius : ", minor_radius)
        if is_plasma:
            plasma_torus = Torus(
                r_0=major_radius, a=minor_radius, wire=False, degrees=FULL_REVOLVE
            )
            is_plasma = False  # Reset flag after creating plasma
            reactor_components.append(
                {"name": component_name, "component": plasma_torus.torus}
            )
        else:
            # Create torus components for the remaining elements
            torus_component = Torus(
                r_0=major_radius, a=minor_radius, wire=False, degrees=HALF_REVOLVE
            )
            reactor_components.append(
                {"name": component_name, "component": torus_component.torus}
            )
            vessel_r_points, vessel_z_points = torus_component.get_r_and_z_points()

            # Calculate vessel dimensions
            vessel_top = max(vessel_z_points)
            vessel_bottom = min(vessel_z_points)
            vessel_height = vessel_top - vessel_bottom

    # Generate and position TF coils using specified radii and computed vessel dimensions
    vessel_minor_radius = accumulated_radii[-1]
    # print("VESSEL MAJOR?")
    # print(vessel_minor_radius)
    filepath = write_csv(vessel_r_points, vessel_z_points)
    tf_coils = tf_step(vessel_minor_radius, filepath,
                       tf_dz, tf_dr, tf_coil_path)

    # At the very end of your code, after you've used the .csv files
    file_paths_to_delete = ["outer.csv", "inner.csv"]
    delete_csv_files(file_paths_to_delete)
    print("TF RESTORED")

    # Constants for coil position calculations to avoid clipping with the reactor structure
    top_coil_ratio = 1 / 8
    bottom_coil_ratio = 1 / 8
    outer_shift = 0.1
    min_outer_rad = major_radius + vessel_minor_radius + tf_dr + (0.5 * pf_dr)
    offset_x = [
        min_outer_rad + outer_shift,
        min_outer_rad + outer_shift,
        min_outer_rad + outer_shift,
    ]  # X-axis offsets for coils
    max_inner_rad = major_radius - vessel_minor_radius - tf_dr - (0.5 * pf_dr)
    inner_offsets = [
        max_inner_rad / 4,
        max_inner_rad / 2,
        max_inner_rad,
        2 * max_inner_rad,
        4 * max_inner_rad,
    ]  # Specific offsets for inner coils
    print("INNER OFFSETS:", inner_offsets)

    # Calculate coil positions using vessel dimensions and ratios
    coil_positions = {
        "top_coils": np.linspace((vessel_height / 8), (vessel_height / 3), 3),
        "bottom_coils": np.linspace((-vessel_height / 8), (-vessel_height / 3), 3),
        "top_inner_coils": np.append(
            np.linspace(
                vessel_height / 3, vessel_top +
                (vessel_top * top_coil_ratio), 4
            ),
            vessel_top + vessel_top * top_coil_ratio,
        ),
        "bottom_inner_coils": np.append(
            np.linspace(
                -vessel_height / 3,
                vessel_bottom - (abs(vessel_bottom) * bottom_coil_ratio),
                4,
            ),
            vessel_bottom - abs(vessel_bottom) * bottom_coil_ratio,
        ),
    }

    # print("Coil pos")
    print("Vessel height: ", vessel_height)
    print(coil_positions)

    # Offsets for coil placement to ensure correct positioning
    offsets = {"x_offsets": offset_x, "inner_offsets": inner_offsets}

    # This nested function generates a set of coils based on the provided parameters
    def generate_coils(
        tf_dr, pf_dr, pf_dz, positions, offsets, is_inner_coil=False, is_top=True
    ):
        """
        Generate a set of PF (Poloidal Field) coils for a tokamak.

        Parameters:
        - positions (array): The calculated positions for the coils.
        - offsets (list): The offset ratios to apply to each coil to minimize clipping.
        - is_inner_coil (bool): Flag to determine if the coils are inner coils.
        - is_top (bool): Flag to determine if the coils are positioned on the top.

        Returns:
        - A set of coils generated by the `generate_pf_coil_set` function.
        """
        return generate_pf_coil_set(
            positions,
            offsets,
            vessel_minor_radius,
            tf_dr,
            pf_dr,
            pf_dz,
            major_radius,
            inner_coil=is_inner_coil,
            top=is_top,
            pf_coil_path=pf_coil_path
        )

    # ADD RADIAL BUILD COMPONENTS

    # Cut the components from each other to ensure proper assembly
    for i in range(1, len(reactor_components)):
        reactor_components[i]["component"] = reactor_components[i]["component"].cut(
            reactor_components[i - 1]["component"]
        )

    # Add all components to the final assembly
    for part in reactor_components:
        tokamak_assembly.add(part["component"], name=part["name"])
        reactor_only.add(part["component"], name=part["name"])
        print(f"Added {part['name']} to the reactor.")

    # Explicitly iterate over coil positions to generate and add coils to the assemblies
    for position_label, positions in coil_positions.items():
        offsets_key = "inner_offsets" if "inner" in position_label else "x_offsets"
        is_inner_coil = "inner" in position_label
        is_top = "top" in position_label
        print(coil_positions.items())
        coil_set = generate_coils(
            tf_dr, pf_dr, pf_dz, positions, offsets[offsets_key], is_inner_coil, is_top
        )
        print("COIL POS")
        print(coil_positions.items())
        print("min inner coil height: ", min(
            coil_positions.get("top_inner_coils")))
        print("Solenoid height : ",
              (2 * (min(coil_positions.get("top_inner_coils")))))
        sol_height = 2 * (min(coil_positions.get("top_inner_coils")))
        if sol:
            solenoid_coils = generate_solenoid(
                solenoid_length=sol_height,
                number_of_turns=40,
                loop_radius=0.08,
                solenoid_thickness=0.1
            )
        print("Generating coils")

        # Add each coil to the assemblies with a unique name
        for i, coil in enumerate(coil_set):
            coil_name = f"{position_label}_{i}"
            tokamak_assembly.add(coil, name=coil_name)
            coils.add(coil, name=coil_name)

        # Add solenoid coils to the assemblies
        if sol:
            for i, s_coil in enumerate(solenoid_coils):
                solenoid_coil_name = f"solenoid_{position_label}_{i}"
                tokamak_assembly.add(s_coil, name=solenoid_coil_name)
                coils.add(s_coil, name=solenoid_coil_name)
                print(f"Added {solenoid_coil_name} to the reactor.")

    # The tokamak assembly with and without the coils
    tokamak_assembly.add(tf_coils, name="TF_coils")
    coils.add(tf_coils, name="TF_coils")
    return tokamak_assembly, coils, reactor_only
