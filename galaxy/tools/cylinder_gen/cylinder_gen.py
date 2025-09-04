# pylint: disable=redefined-outer-name
# pylint: disable=import-error
"""
This module contains the `REBCOCoilDesign` class which is used for designing
REBCO (Rare-Earth Barium Copper Oxide) coils. 

The class provides methods for defining the coil geometry, optimizing the coil
design, and generating a 3D model of the coil.

The module also includes functionality for parsing command-line arguments and
reading parameters from a JSON file. This allows the coil design parameters to
be easily specified and modified.

Dependencies:
    argparse: A standard library module for parsing command-line arguments.
    json: A standard library module for working with JSON data.
    cadquery: A Python library for building parametric 3D CAD models.
    numpy: A library for numerical computing with Python.
    scipy: A library for scientific computing with Python.
"""

import argparse
import json
import cadquery as cq
import numpy as np
from scipy.optimize import minimize


class REBCOCoilDesign:
    """
    A class used to design REBCO (Rare-Earth Barium Copper Oxide) coils.

    The class provides methods for defining the coil geometry, optimizing the coil
    design, and generating a 3D model of the coil.

    Attributes:
    mu_0 (float): Vacuum permeability.
    B_target (float): Target magnetic field.
    workplane (str): The workplane for the 3D model.
    ybco_rho (float): Density of YBCO.
    critical_current_density (float): Critical current density of YBCO.
    max_supply_current (float): Maximum supply current for the coil.
    ybco_cost (float): Cost per unit volume of YBCO.
    cu_cost (float): Cost per unit volume of copper.
    ss_cost (float): Cost per unit volume of stainless steel.
    ybco_cs (float): Cross-sectional area of YBCO.
    coolant_cs (float): Cross-sectional area of coolant.
    cu_cs (float): Cross-sectional area of copper.
    ss_cs (float): Cross-sectional area of stainless steel.
    min_i_rad (float): Minimum inner radius of the coil.
    r_center (float): Radius of the center of the coil.
    dr (float): Radial build of the coil.
    dz (float): Height of the coil.
    """
    mu_0 = 4 * np.pi * 10**-7  # vacuum permeability
    B_target = 9  # T, target magnetic field

    def __init__(
        self,
        workplane="XY",
        ybco_rho=6200,
        critical_current_density=1e10,
        max_supply_current=16.786e4,
        ybco_cost=100,
        cu_cost=10.3,
        ss_cost=5,
        ybco_cs=0.00009,
        coolant_cs=0.000009,
        cu_cs=0.000031,
        ss_cs=0.000108,
        min_i_rad=4.93,
        r_center=0.18,
        dr=0.1,
        dz=0.1,
        z_center=0,
        max_supply_current_2=16.786e6,
    ):
        self.workplane = workplane
        self.ybco_rho = ybco_rho
        self.critical_current_density = critical_current_density
        self.max_supply_current = max_supply_current
        self.ybco_cost = ybco_cost
        self.cu_cost = cu_cost
        self.ss_cost = ss_cost
        self.ybco_cs = ybco_cs
        self.coolant_cs = coolant_cs
        self.cu_cs = cu_cs
        self.ss_cs = ss_cs
        self.total_cs = ybco_cs + coolant_cs + cu_cs + ss_cs
        self.min_i_rad = min_i_rad
        self.turn_thickness = np.sqrt(self.total_cs)
        self.r_center = r_center
        self.z_center = z_center
        self.dr = dr
        self.dz = dz
        self.max_supply_current = max_supply_current_2
        self.max_allowable_current = min(
            self.max_supply_current, self.critical_current_density / 3 * self.ybco_cs
        )

        self.coil = self.make_coil()

    def num_turns(self, params):
        """
        Calculates the number of turns in the coil based on the average radius and current.

        Parameters:
        params (tuple): A tuple containing the current (float) 
        and the average radius (float) of the coil.

        Returns:
        float: The number of turns in the coil.
        """
        current, r_avg = params
        return 2 * r_avg * self.B_target / (self.mu_0 * current)

    def wire_length(self, params):
        """
        Calculates the length of the wire in the coil.

        Parameters:
        params (tuple): A tuple containing the current (float) 
        and the average radius (float) of the coil.

        Returns:
        float: The length of the wire in the coil.
        """
        _, r_avg = params
        n = self.num_turns(params)
        return 2 * np.pi * r_avg * n

    def current_constraint(self, params):
        """
        Calculates the difference between the current and the maximum allowable current.

        Parameters:
        params (tuple): A tuple containing the current (float) 
        and the average radius (float) of the coil.

        Returns:
        float: The difference between the current and the maximum allowable current.
        """
        current, _ = params
        return current - self.max_allowable_current

    def turns_constraint(self, params):
        """
        Calculates the difference between the number of turns and the nearest integer value of turns

        Parameters:
        params (tuple): A tuple containing the current (float) 
        and the average radius (float) of the coil.

        Returns:
        float: The difference between the number of turns and the nearest integer value of turns.
        """
        n = self.num_turns(params)
        return n - np.round(n)

    def inner_radius_constraint(self, params):
        """
        Calculates the difference between the inner radius of the coil 
        and the minimum allowable inner radius.

        Parameters:
        params (tuple): A tuple containing the current (float) 
        and the average radius (float) of the coil.

        Returns:
        float: The difference between the inner radius of the coil 
        and the minimum allowable inner radius.
        """
        _, r_avg = params
        n = self.num_turns(params)
        i_rad = r_avg - 0.5 * n * self.turn_thickness
        return i_rad - self.min_i_rad

    def compute(self):
        """
        Computes the optimal parameters for the coil design by minimizing the wire length.

        The function uses the scipy.optimize.minimize function with the 'SLSQP' method 
        (Sequential Least Squares Programming) which allows for bounds and constraint optimization.

        The constraints are defined as follows:
        - The current must be equal to the maximum allowable current.
        - The number of turns must be an integer.
        - The inner radius of the coil must be greater than or 
          equal to the minimum allowable inner radius.

        The bounds are defined as follows:
        - The current must be greater than or equal to 1.
        - The average radius of the coil must be greater than or equal to the minimum inner radius.

        The initial guess for the optimization is the maximum allowable current
        and the minimum inner radius.

        The result of the optimization is stored in the 'result' attribute of the class instance.

        Returns:
        None
        """
        bnds = ((1, None), (self.min_i_rad, None))
        initial_guess = [self.max_allowable_current, self.min_i_rad]

        cons = (
            {"type": "eq", "fun": self.current_constraint},
            {"type": "eq", "fun": self.turns_constraint},
            {"type": "ineq", "fun": self.inner_radius_constraint},
        )

        self.result = minimize(
            self.wire_length, initial_guess, bounds=bnds, constraints=cons
        )

    def make_coil(self):
        """
        Creates a coil based on the optimal parameters computed by the 'compute' method.

        The function calculates the number of turns and the inner radius of the coil based on the 
        optimal parameters. It then creates a coil with these parameters and calculates the radii 
        of the coil.

        The function also calculates the total cost of the coil.

        Returns:
        coil (object): The created coil object.
        coil_radii (list): The radii of the coil.
        """
        self.compute()
      #  N = self.num_turns(self.result.x)
        r_center = self.r_center
        z_center = self.z_center
        dr = self.dr
        dz = self.dz
        i_rad = r_center - (0.5 * dr)
        o_rad = r_center + (0.5 * dr)
        z_max = z_center + (0.5 * dz)
        height = dz

        print("COIL VALS")
        print(r_center, z_center, height, z_max)
        print(self.workplane)

        outer_coil = cq.Workplane(self.workplane).circle(o_rad).extrude(height)
        inner_coil = cq.Workplane(self.workplane).circle(i_rad).extrude(height)
        outer_coil = outer_coil.translate((0, z_max, 0))
        inner_coil = inner_coil.translate((0, z_max, 0))
        radii = [i_rad, o_rad]
        coil = outer_coil.cut(inner_coil)
        # display(coil)
        return coil, radii
        # display(coil)

    def calculate_cost(self):
        """
        Calculates the total cost of the coil.

        The function calculates the cost of the YBCO, copper, 
        and stainless steel components of the coil 
        based on the wire length and the cost per unit volume of each material. 

        The total cost is the sum of the costs of the YBCO, copper, and stainless steel components, 
        multiplied by a factor of 9 to account for manufacturing costs.

        The total cost is stored in the 'total_cost' attribute of the class instance.

        Returns:
        None
        """
        final_ybco_cost = (
            self.wire_length(self.result.x)
            * self.ybco_cs
            / self.total_cs
            * self.ybco_cost
            * 1e-6
        )
        final_cu_cost = self.result.fun * self.cu_cs * self.cu_cost * 7900 * 1e-6
        final_ss_cost = self.result.fun * self.ss_cs * self.ss_cost * 7900 * 1e-6
        tot_mat_cost = final_ybco_cost + final_cu_cost + final_ss_cost
        self.total_cost = round(tot_mat_cost * 9, 3)

    def print_results(self):
        """
        Prints the results of the coil design.

        The function first calls the 'compute' method to 
        calculate the optimal parameters for the coil design.
        It then calculates various parameters of the coil, 
        such as the inner and outer radius, height, 
        current density, and number of turns, based on the optimal parameters.

        The function also calculates the cost of the YBCO, copper, 
        and stainless steel components of the coil.

        All these results are then printed to the console.

        Returns:
        None
        """
        self.compute()
        n = self.num_turns(self.result.x)
        i_rad = self.result.x[1] - 0.5 * np.sqrt(n) * self.turn_thickness
        o_rad = self.result.x[1] + 0.5 * np.sqrt(n) * self.turn_thickness
        height = np.sqrt(n) * self.turn_thickness
        current_density = self.result.x[0] / self.ybco_cs

        print(
            "\n--------------------------------RESULTS--------------------------------\n"
        )

        # PARAMETERS
        print("Field at center:", self.B_target, "T \n")
        print("Current:", round(self.result.x[0], 3), "A")
        print("Current Density:", round(current_density, 3), "A/m^2")
        print("Inner radius:", round(i_rad, 3), "m")
        print("Outer radius:", round(o_rad, 3), "m")
        print("Height:", round(height, 3), "m")
        print("Number of turns:", round(n))
        print("Length of wire:", round(self.wire_length(self.result.x), 2), "m\n")

        # COST
        final_ybco_cost = (
            self.wire_length(self.result.x)
            * self.ybco_cs
            / self.total_cs
            * self.ybco_cost
            * 1e-6
        )
        final_cu_cost = self.result.fun * self.cu_cs * self.cu_cost * 7900 * 1e-6
        final_ss_cost = self.result.fun * self.ss_cs * self.ss_cost * 7900 * 1e-6
        print("Cost of YBCO: $", round(final_ybco_cost, 3), "M")
        print("Cost of copper: $", round(final_cu_cost, 3), "M")
        print("Cost of steel: $", round(final_ss_cost, 3), "M")

        tot_mat_cost = final_ybco_cost + final_cu_cost + final_ss_cost
        print("Total material cost: $", round(tot_mat_cost, 3), "M")
        print("Cost to manufacture w/ mfr factor 9: $",
              round(tot_mat_cost * 9, 3), "M")
        self.total_cost = round(tot_mat_cost * 9, 3)

    def append_text_file(self, file_path):
        """
        Appends the coil parameters to a text file.

        The function first calls the 'compute' method to 
        calculate the optimal parameters for the coil design.
        It then calculates the average radius, number of turns, 
        and current based on the optimal parameters.

        These parameters, along with the coordinates of the center of the coil, 
        are then written to the text file 
        specified by 'file_path'. Each parameter is separated by a comma, 
        and each set of parameters is written 
        on a new line.

        Parameters:
        file_path (str): The path to the text file to which the coil parameters will be appended.

        Returns:
        None
        """
        self.compute()
        r_avg = (i_rad + o_rad) / 2
        turns = round(n)
        current = round(self.result.x[0], 3)

        with open(file_path, "a", encoding='utf-8') as file:
            file.write(
                f"{r_avg},{turns},{current},{self.r_center},{self.z_center}\n")


class Cylinder:
    """
    A class used to represent a Cylinder.

    The class provides methods for defining the cylinder geometry, calculating its volume, 
    and generating a 3D model of the cylinder.

    Attributes:
    radius (float): The radius of the cylinder.
    height (float): The height of the cylinder.
    """

    def __init__(self, radial_build, height):
        reactor = cq.Assembly()
        outer_radius = 0
        layers = []
        i = 0
        while i <= 3:
            print(radial_build[i], type(radial_build[i]))
            outer_radius += round(float(radial_build[i]), 2)
            print("outer radius")
            print(outer_radius, round(
                float(radial_build[i]), 2), (radial_build[i]))
            if i == 0:
                cylinder = (
                    cq.Workplane("XY")
                    .cylinder(height, radial_build[i])
                )
                layers.append(cylinder)
            else:
                inner_radius = outer_prev
                cylinder = self.generate_hollow_cylinder(
                    height, outer_radius, inner_radius)
                layers.append(cylinder)
            reactor.add(cylinder)
            self.reactor = reactor
            self.layers = layers
            outer_prev = outer_radius
            i = i+1

    def generate_hollow_cylinder(self, height, outer_radius, inner_radius):
        """
        Generates a 3D model of a hollow cylinder using CadQuery.

        Parameters:
        height (float): The height of the cylinder.
        outer_radius (float): The outer radius of the cylinder.
        inner_radius (float): The inner radius of the cylinder.

        Returns:
        cylinder (CadQuery object): The 3D model of the hollow cylinder.
        """

        if outer_radius <= inner_radius:
            raise ValueError("outer_radius must be larger than inner_radius")

        cylinder1 = (
            cq.Workplane("XY")
            .cylinder(height, outer_radius)
        )
        cylinder2 = (
            cq.Workplane("XY")
            .cylinder(height, inner_radius)
        )

        cylinder = cylinder1.cut(cylinder2)
        print("radii: ", inner_radius, outer_radius)

        return cylinder


def make_coil(min_i_rad, current):
    """
    Creates a coil design and calculates its cost.

    Parameters:
    min_i_rad (float): The minimum inner radius of the coil.
    current (float): The maximum supply current for the coil.

    Returns:
    coil (object): The created coil object.
    coil_radii (list): The radii of the coil.
    result (object): The result of the coil design.
    coil_cost (float): The total cost of the coil.
    """
    coil_design = REBCOCoilDesign(
        min_i_rad=min_i_rad, workplane="XY", max_supply_current=current)
    result = coil_design.result
    coil_design.calculate_cost()
    coil_cost = coil_design.total_cost
    coil, coil_radii = coil_design.make_coil()

    return coil, coil_radii, result, coil_cost


def generate_cylinder(radial_build, height, n_coils, inner_radius, current, output_filepath):
    """
    Generates a cylinder with a specified number of coils and calculates the total cost.

    Parameters:
    radial_build (float): The radial build of the cylinder.
    height (float): The height of the cylinder.
    n_coils (int): The number of coils in the cylinder.
    inner_radius (float): The inner radius of the coil.
    current (float): The maximum supply current for the coil.
    output_filepath (str): The path to the output file where the coil info will be written.

    Returns:
    None. The function writes coil info to a CSV file and prints the total cost of each coil.
    """
    total_cost = 0
    count = 0
    cylinder = Cylinder(radial_build, height)

    # for i,layer in enumerate(cylinder.layers):
    #     layer.val().exportStep(f"data/geometry_data/Cylindrical/layer{i}.step")

    coil_z = np.linspace(-height/2, height/2, n_coils)

    # Write coil info to csv file

    coils = cq.Assembly()

    with open(output_filepath, "w", encoding='utf-8') as file:
        file.write(
            "N,I (A),Inner Radius,Outer radius,Coil_X,Coil_Y,Coil_Z,Normal X,Normal Y,Normal Z \n")

        for coil_z in coil_z:
            coil, _, _, coil_cost = make_coil(
                inner_radius, current)
            outer_radius = inner_radius + (0.1 * inner_radius)
            coil = coil.translate(cq.Vector(0, 0, coil_z))
            total_cost += coil_cost
            print("Total Cost of Coil", count, "is:", coil_cost)
            cylinder.reactor.add(coil)
            coils.add(coil)
            count += 1
            if count == 1:
                i_val = 10*current
            elif count == 1:
                i_val = 10*current
            else:
                i_val = current

            file.write(
                f"1,{i_val},{inner_radius},{outer_radius},0,0,{coil_z},0,0,1\n")

        # print("Count : ",count,N_coils)
        cylinder.reactor.save("reactor.step")
        coils.save("coils.step")
        print("Total Cost of all Coils is:", total_cost)
        return cylinder


parser = argparse.ArgumentParser()
parser.add_argument('file_path')
parser.add_argument('output_filepath')
args = parser.parse_args()
file_path = args.file_path
output_csv = args.output_filepath
# Open the file and load the data
with open(file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Now, assign the values to variables
# Assuming your data is under the 'geometry' key
geometry_data = data['geometry']
radial_build = geometry_data['radial_build']
reactor_height = geometry_data['height']
coil_num = geometry_data['number_of_coils']
current = geometry_data['current']


inner_radius = sum(radial_build)+3

generate_cylinder(radial_build, reactor_height, coil_num,
                  inner_radius, current, output_csv)
