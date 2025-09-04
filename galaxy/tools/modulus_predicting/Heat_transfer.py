import torch
import numpy as np
from sympy import Symbol, Eq, Function, Number, exp, simplify

import modulus.sym
from modulus.sym.hydra import to_absolute_path, ModulusConfig, instantiate_arch
from modulus.sym.solver import Solver
from modulus.sym.domain import Domain
from modulus.sym.geometry.primitives_1d import Line1D
from modulus.sym.domain.constraint import (
    PointwiseBoundaryConstraint,
    PointwiseInteriorConstraint,
    PointwiseConstraint
)
from modulus.sym.domain.validator import PointwiseValidator
from modulus.sym.domain.monitor import PointwiseMonitor
from modulus.sym.key import Key
from modulus.sym.node import Node
from modulus.sym.eq.pde import PDE
from modulus.sym.geometry.primitives_3d import Box, Plane
from modulus.sym.geometry.tessellation import Tessellation
from modulus.sym.eq.pdes.navier_stokes import GradNormal
from modulus.sym.domain.inferencer import PointwiseInferencer
from modulus.sym.models.modified_fourier_net import ModifiedFourierNetArch
from modulus.sym.domain.inferencer import PointVTKInferencer
from modulus.sym.utils.io import (
    VTKUniformGrid,
)
from modulus.sym.utils.io import csv_to_dict
import math
from modulus.sym.models.multiscale_fourier_net import MultiscaleFourierNetArch

import os
cwd = os.getcwd()
print(f'pwd:{cwd}')

reactorwall = Tessellation.from_stl("reactorWall.STL", airtight=True).scale(0.01)
reactorwall_inner_sur = Tessellation.from_stl("reactorWallInner.STL", airtight=False).scale(0.01)
reactorwall_outer_sur = Tessellation.from_stl("reactorWallOuter.STL", airtight=False).scale(0.01)
reactorwall_side = Tessellation.from_stl("reactorWallSide.STL", airtight=False).scale(0.01)


D1 = 25
D2 = 25
rho1=1850
rho2=7700
sp_h1=0.45
sp_h2=1.8
film_coeff=20
epsilon1=0.3
epsilon2=0.7
Tamb1 = 20
Tamb2 = 1000


class Diffusion(PDE):
    name = "Diffusion"

    def __init__(self, T="T", D="D", Q=0, dim=3, time=True):
        # set params
        self.T = T
        self.dim = dim
        self.time = time

        # coordinates
        x, y, z = Symbol("x"), Symbol("y"), Symbol("z")

        # time
        t = Symbol("t")

        # make input variables
        input_variables = {"x": x, "y": y, "z": z, "t": t}
        if self.dim == 1:
            input_variables.pop("y")
            input_variables.pop("z")
        elif self.dim == 2:
            input_variables.pop("z")
        if not self.time:
            input_variables.pop("t")

        # Temperature
        assert type(T) == str, "T needs to be string"
        T = Function(T)(*input_variables)

        # Diffusivity
        if type(D) is str:
            D = Function(D)(*input_variables)
        elif type(D) in [float, int]:
            D = Number(D)

        # Source
        if type(Q) is str:
            Q = Function(Q)(*input_variables)
        elif type(Q) in [float, int]:
            Q = Number(Q)

        # set equations
        self.equations = {}
        self.equations["diffusion_" + self.T] = (
            T.diff(t)
            - (D * T.diff(x)).diff(x)
            - (D * T.diff(y)).diff(y)
            - (D * T.diff(z)).diff(z)
            - Q
        )
class BCiDiffusion(PDE):
    name = "Diffusion"

    def __init__(self, T="T", D="D", Q=0, rho="rho", c="c", film_coeff=0, epsilon=0, sigma=5.67e-8, T_amb=0, dim=3, time=True):
        # set params
        self.T = T
        self.dim = dim
        self.time = time

        # coordinates
        x, y, z = Symbol("x"), Symbol("y"), Symbol("z")
        normal_x, normal_y, normal_z = (
            Symbol("normal_x"),
            Symbol("normal_y"),
            Symbol("normal_z"),
        )
        # time
        t = Symbol("t")

        # make input variables
        input_variables = {"x": x, "y": y, "z": z, "t": t}
        if self.dim == 1:
            input_variables.pop("y")
            input_variables.pop("z")
        elif self.dim == 2:
            input_variables.pop("z")
        if not self.time:
            input_variables.pop("t")

        # Temperature
        assert type(T) == str, "T needs to be string"
        T = Function(T)(*input_variables)

        # Diffusivity
        if type(D) is str:
            D = Function(D)(*input_variables)
        elif type(D) in [float, int]:
            D = Number(D)

        # Source
        if type(Q) is str:
            Q = Function(Q)(*input_variables)
        elif type(Q) in [float, int]:
            Q = Number(Q)

        # Density
        if type(rho) is str:
            rho = Function(rho)(*input_variables)
        elif type(rho) in [float, int]:
            rho = Number(rho)

        # Heat capacity
        if type(c) is str:
            c = Function(c)(*input_variables)
        elif type(c) in [float, int]:
            c = Number(c)

        # Convective heat transfer coefficient
        if type(film_coeff) is str:
            film_coeff = Function(film_coeff)(*input_variables)
        elif type(film_coeff) in [float, int]:
            film_coeff = Number(film_coeff)

        # Ambient temperature
        if type(T_amb) is str:
            T_amb = Function(T_amb)(*input_variables)
        elif type(T_amb) in [float, int]:
            T_amb = Number(T_amb)

        # Emissivity
        if type(epsilon) is str:
            epsilon = Function(epsilon)(*input_variables)
        elif type(epsilon) in [float, int]:
            epsilon = Number(epsilon)
          
        # set equations
        self.equations = {}
        convective = film_coeff * (T - T_amb)
        radiation = epsilon * sigma * ((T + 273.15)**4 - (T_amb + 273.15)**4)
        flux = D * (
            normal_x * T.diff(x) + normal_y * T.diff(y) + normal_z * T.diff(z)
        )
        self.equations["BCidiffusion_" + self.T] = (
            - flux - convective - radiation
        )

class BCoDiffusion(PDE):
    name = "Diffusion"

    def __init__(self, T="T", D="D", Q=0, rho="rho", c="c", film_coeff=0, epsilon=0, sigma=5.67e-8, T_amb=0, dim=3, time=True):
        # set params
        self.T = T
        self.dim = dim
        self.time = time

        # coordinates
        x, y, z = Symbol("x"), Symbol("y"), Symbol("z")
        normal_x, normal_y, normal_z = (
            Symbol("normal_x"),
            Symbol("normal_y"),
            Symbol("normal_z"),
        )
        # time
        t = Symbol("t")

        # make input variables
        input_variables = {"x": x, "y": y, "z": z, "t": t}
        if self.dim == 1:
            input_variables.pop("y")
            input_variables.pop("z")
        elif self.dim == 2:
            input_variables.pop("z")
        if not self.time:
            input_variables.pop("t")

        # Temperature
        assert type(T) == str, "T needs to be string"
        T = Function(T)(*input_variables)

        # Diffusivity
        if type(D) is str:
            D = Function(D)(*input_variables)
        elif type(D) in [float, int]:
            D = Number(D)

        # Source
        if type(Q) is str:
            Q = Function(Q)(*input_variables)
        elif type(Q) in [float, int]:
            Q = Number(Q)

        # Density
        if type(rho) is str:
            rho = Function(rho)(*input_variables)
        elif type(rho) in [float, int]:
            rho = Number(rho)

        # Heat capacity
        if type(c) is str:
            c = Function(c)(*input_variables)
        elif type(c) in [float, int]:
            c = Number(c)

        # Convective heat transfer coefficient
        if type(film_coeff) is str:
            film_coeff = Function(film_coeff)(*input_variables)
        elif type(film_coeff) in [float, int]:
            film_coeff = Number(film_coeff)

        # Ambient temperature
        if type(T_amb) is str:
            T_amb = Function(T_amb)(*input_variables)
        elif type(T_amb) in [float, int]:
            T_amb = Number(T_amb)

        # Emissivity
        if type(epsilon) is str:
            epsilon = Function(epsilon)(*input_variables)
        elif type(epsilon) in [float, int]:
            epsilon = Number(epsilon)

        # set equations
        self.equations = {}
        convective = film_coeff * (T - T_amb)
        radiation = epsilon * sigma * ((T + 273.15)**4 - (T_amb + 273.15)**4)
        flux = D * (
            normal_x * T.diff(x) + normal_y * T.diff(y) + normal_z * T.diff(z)
        )
        self.equations["BCodiffusion_" + self.T] = (
            - flux - convective - radiation
        )
class DiffusionInterface(PDE):
    name = "DiffusionInterface"

    def __init__(self, T_1, T_2, D_1, D_2, dim=3, time=True):
        # set params
        self.T_1 = T_1
        self.T_2 = T_2
        self.dim = dim
        self.time = time

        # coordinates
        x, y, z = Symbol("x"), Symbol("y"), Symbol("z")
        normal_x, normal_y, normal_z = (
            Symbol("normal_x"),
            Symbol("normal_y"),
            Symbol("normal_z"),
        )

        # time
        t = Symbol("t")

        # make input variables
        input_variables = {"x": x, "y": y, "z": z, "t": t}
        if self.dim == 1:
            input_variables.pop("y")
            input_variables.pop("z")
        elif self.dim == 2:
            input_variables.pop("z")
        if not self.time:
            input_variables.pop("t")

        # Diffusivity
        if type(D_1) is str:
            D_1 = Function(D_1)(*input_variables)
        elif type(D_1) in [float, int]:
            D_1 = Number(D_1)
        if type(D_2) is str:
            D_2 = Function(D_2)(*input_variables)
        elif type(D_2) in [float, int]:
            D_2 = Number(D_2)

        # variables to match the boundary conditions (example Temperature)
        T_1 = Function(T_1)(*input_variables)
        T_2 = Function(T_2)(*input_variables)

        # set equations
        self.equations = {}
        self.equations["diffusion_interface_dirichlet_" + self.T_1 + "_" + self.T_2] = (
            T_1 - T_2
        )
        flux_1 = D_1 * (
            normal_x * T_1.diff(x) + normal_y * T_1.diff(y) + normal_z * T_1.diff(z)
        )
        flux_2 = D_2 * (
            normal_x * T_2.diff(x) + normal_y * T_2.diff(y) + normal_z * T_2.diff(z)
        )
        self.equations["diffusion_interface_neumann_" + self.T_1 + "_" + self.T_2] = (
            flux_1 - flux_2
        )

@modulus.sym.main(config_path="./conf", config_name="config")
def run(cfg: ModulusConfig) -> None:
    # make list of nodes to unroll graph on
    PVwall_BCi = BCiDiffusion(T="u_2", D=D1, rho=rho2, c=sp_h2, epsilon=0.7, T_amb=347, dim=3, time=False)
    PVwall_ht = Diffusion(T="u_2", D=D1, dim=3, time=False)
    PVwall_BCo = BCoDiffusion(T="u_2", D=D1, rho=rho2, c=sp_h2, film_coeff=20, T_amb=20, epsilon=0.7, dim=3, time=False)
    gn_theta_f = GradNormal("u_2", dim=3, time=False)
    diff_net_u_2 = MultiscaleFourierNetArch(
        input_keys=[Key("x"), Key("y"), Key("z")],
        output_keys=[Key("u_2_star")],
        frequencies=(("gaussian", 1, 32), ("gaussian", 10, 32),),
        frequencies_params=(("gaussian", 1, 32), ("gaussian", 10, 32),),
    )
    nodes = (
        PVwall_BCi.make_nodes()
        + PVwall_ht.make_nodes()
        + PVwall_BCo.make_nodes()
        + gn_theta_f.make_nodes()
        + [Node.from_sympy(Symbol("u_2_star") +1200 , "u_2")]
        + [diff_net_u_2.make_node(name="u2_network", jit=False)]
    )

    # make domain add constraints to the solver
    domain = Domain()

    # sympy variables
    x = Symbol("x")
    y = Symbol("y")
    z = Symbol("z")
    def constraint1(x, y, z):
        return x**2+y**2>0.1
    def constraint2(x, y, z):
        return x**2+y**2<=0.1
    # left hand side (x = 0) Pt a

    lhs1 = PointwiseBoundaryConstraint(
        nodes=nodes,
        geometry=reactorwall_inner_sur,
        outvar={"BCidiffusion_u_2": 0},
        batch_size=1000,
        lambda_weighting={"BCidiffusion_u_2": 1},
#         criteria=constraint1(x, y, z),
    )
    domain.add_constraint(lhs1, "left_hand_side1")

    # interior 1
    mapping = {
        "x": 0,
        "y": 1,
        "z": 2,
        "Flux": 3,
        "area": 4,
    }

    Flux_data = np.loadtxt(f"{str(cwd)}/interior_points.txt", delimiter=' ', usecols=(mapping.values()))
    sampled_x = np.expand_dims(Flux_data[:, mapping["x"]].flatten(), axis=-1)/100
    sampled_y = np.expand_dims(Flux_data[:, mapping["y"]].flatten(), axis=-1)/100
    sampled_z = np.expand_dims(Flux_data[:, mapping["z"]].flatten(), axis=-1)/100
    sampled_area = np.expand_dims(Flux_data[:, mapping["area"]].flatten(), axis=-1)/1000000 # np.full_like(sampled_x, 0.00001)
    flux = np.expand_dims(Flux_data[:, mapping["Flux"]].flatten(), axis=-1) * 1000000

    # interior
    data = PointwiseConstraint.from_numpy(
        nodes=nodes,
        invar={"x": sampled_x, "y": sampled_y, "z": sampled_z, "area": sampled_area},
        outvar={"diffusion_u_2": flux},
        batch_size=10000,
    )
    domain.add_constraint(data, "interior_data")
    rhs1 = PointwiseBoundaryConstraint(
        nodes=nodes,
        geometry=reactorwall_outer_sur,
        outvar={"BCodiffusion_u_2": 0},
        batch_size=1000,
        lambda_weighting={"BCodiffusion_u_2": 1},
    )
    domain.add_constraint(rhs1, "right_hand_side1")

    lhs2 = PointwiseBoundaryConstraint(
        nodes=nodes,
        geometry=reactorwall_side,
        outvar={"normal_gradient_u_2": 0},
        batch_size=500,
        lambda_weighting={"normal_gradient_u_2": 1000},
    )
    domain.add_constraint(lhs2, "left_hand_side2")

    mapping = {
        "x": 0,
        "y": 1,
        "z": 2,
        "Flux": 3,
        # "area": 4,
    }

    Flux_data = np.loadtxt(f"{str(cwd)}/heat_flux.txt", delimiter=' ', usecols=(mapping.values()))
    sampled_x = np.expand_dims(Flux_data[:, mapping["x"]].flatten(), axis=-1)/100
    sampled_y = np.expand_dims(Flux_data[:, mapping["y"]].flatten(), axis=-1)/100
    sampled_z = np.expand_dims(Flux_data[:, mapping["z"]].flatten(), axis=-1)/100
    # sampled_sdf = np.expand_dims(Flux_data[:, mapping["sdf"]].flatten(), axis=-1)
    # TODO: Area not currently being calculated in sample points generator
    sampled_area = np.full_like(sampled_x, 0.00001)  # np.expand_dims(Flux_data[:, mapping["area"]].flatten(), axis=-1)
    flux = np.expand_dims(Flux_data[:, mapping["Flux"]].flatten(), axis=-1) * 1000000
    inference = PointwiseInferencer(
        nodes=nodes,
        invar={"x": sampled_x, "y": sampled_y, "z": sampled_z},
        output_names=["u_2"],
    )
    domain.add_inferencer(inference, "output")

    # make solver
    slv = Solver(cfg, domain)

    # start solver
    slv.solve()


if __name__ == "__main__":
    run()
