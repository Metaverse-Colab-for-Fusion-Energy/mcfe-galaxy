import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from contourpy import contour_generator
from contourpy.util.mpl_renderer import MplRenderer as Renderer
import os
import argparse


def coil_coord_gen(regcoil_p, nescin_p, coils_per_p, p, thickness):
    os.makedirs("coords", exist_ok=True)
    regcoilFilenames = regcoil_p
    nescinFilenames = nescin_p

    coilsPerHalfPeriod = int(coils_per_p / 2)
    numHalfPeriodsToPlot = int(p * 2)

    coil_thickness = thickness / 2

    colors = np.array([[1, 0, 0],
                       [1, 0.7, 0],
                       [0, 0.8, 0],
                       [0, 0, 1],
                       [1, 0, 1]])

    ntheta = 128
    nzeta = 128

    for whichFile in range(1):
        # Read regcoil_out file:
        filename = regcoilFilenames
        print('Reading', filename)

        with nc.Dataset(filename, 'r') as f:
            nfp = f.variables['nfp'][:]
            chi2_B = f.variables['chi2_B'][:]
            chi2_K = f.variables['chi2_K'][:]
            ilambda = chi2_B.shape[0]

            net_poloidal_current_Amperes = f.variables['net_poloidal_current_Amperes'][:]

            theta = f.variables['theta_coil'][:]
            nzeta = f.variables['nzeta_coil'][:]
            nzetal = nzeta * nfp
            zetal = np.linspace(0, 2 * np.pi, nzetal + 1)
            zetal = zetal[:-1]
            zetal_2D, theta_2D = np.meshgrid(zetal, theta)
            potential0 = f.variables['current_potential'][:]

            #   print(potential0[0,:,:])
            potential1 = potential0[ilambda - 1, :, :]

            potential1 = np.transpose(potential1)
            potential = np.kron(np.ones((1, nfp)), potential1) + np.kron(
                ((np.arange(1, nfp + 1) - 1) * net_poloidal_current_Amperes / nfp), np.ones((len(theta), nzeta)))

            potential = potential / net_poloidal_current_Amperes * nfp

        # SUCCESSFULLY COVERTED ALL ABOVE

        # Read surface from nescin file:
        filename = nescinFilenames
        print('Reading', filename)
        with open(filename, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if '------ Current Surface:' in line:
                    break
            mnmax_nescin = int(lines[i + 2])

            xm_nescin = np.zeros(mnmax_nescin)
            xn_nescin = np.zeros(mnmax_nescin)
            rmnc_nescin = np.zeros(mnmax_nescin)
            zmns_nescin = np.zeros(mnmax_nescin)
            for j in range(1, mnmax_nescin):
                data = lines[i + 4 + j].split()

                xm_nescin[j] = int(data[0])
                xn_nescin[j] = int(data[1])
                rmnc_nescin[j] = float(data[2])
                zmns_nescin[j] = float(data[3])

        contours = np.linspace(0, nfp, coilsPerHalfPeriod * 2 * nfp + 1)
        dc = contours[1] - contours[0]
        contours_old = contours + 0.5 * dc

        contours = []
        for con_c in range(coilsPerHalfPeriod * numHalfPeriodsToPlot):
            contours.append(contours_old[con_c])

        X = []
        Y = []

        for test in range(320):
            X.append(test)
            if test < 64:
                Y.append(test)

        c1 = plt.contourf(zetal_2D, theta_2D, potential, contours)
        c2 = plt.contour(zetal_2D, theta_2D, potential, contours, colors='k')
        plt.xlabel("Zeta")
        plt.ylabel("Theta")

        new_pot = np.transpose(potential)

        plt.clabel(c2, c2.levels, inline=True, fontsize=10)
        print("Potential calculated")

        # Write zeta,theta and potential values to a file:

        #  plt.colorbar(c1)
        plt.title('Current_pot')
        #   plt.show()
        plt.savefig("current_pot.png")

        contours_theta = []
        contours_zeta = []
        contours_x = []
        contours_y = []
        contours_z = []
        contours_dxdtheta = []
        contours_dydtheta = []
        contours_dzdtheta = []
        contours_dxdzeta = []
        contours_dydzeta = []
        contours_dzdzeta = []
        coils_x = []
        coils_y = []
        coils_z = []

        # WORKS UP TO HERE AS OF 14/10/24

        for j in range(coilsPerHalfPeriod * numHalfPeriodsToPlot):
            this_contour = contours[j]

            cont_gen = contour_generator(x=zetal_2D, y=theta_2D, z=potential)
            multi_filled = cont_gen.multi_filled(contours)
            C = cont_gen.lines(this_contour)

            #           print("Setting zeta:")
            for i in range(len(C)):

                zeta_i = C[i][:, 0]
                zeta_i = zeta_i[::-1]
                theta_i = C[i][:, 1]
                theta_i = theta_i[::-1]

                if i == 0:

                    this_zeta = zeta_i
                    this_theta = theta_i
                else:
                    this_zeta = np.hstack((this_zeta, zeta_i))
                    this_theta = np.hstack((this_theta, theta_i))

            contours_zeta.append(np.concatenate((this_zeta, [this_zeta[0]])))
            contours_theta.append(np.concatenate((this_theta, [this_theta[0]])))
            #        plt.plot(contours_zeta[j],contours_theta[j],'r',linewidth=2)
            contours_x.append(np.zeros_like(contours_theta[j]))
            contours_y.append(np.zeros_like(contours_theta[j]))
            contours_z.append(np.zeros_like(contours_theta[j]))
            contours_dxdtheta.append(np.zeros_like(contours_theta[j]))
            contours_dydtheta.append(np.zeros_like(contours_theta[j]))
            contours_dzdtheta.append(np.zeros_like(contours_theta[j]))
            contours_dxdzeta.append(np.zeros_like(contours_theta[j]))
            contours_dydzeta.append(np.zeros_like(contours_theta[j]))
            contours_dzdzeta.append(np.zeros_like(contours_theta[j]))

        x = np.zeros_like(theta_2D)
        y = np.zeros_like(theta_2D)
        z = np.zeros_like(theta_2D)
        dxdtheta = np.zeros_like(theta_2D)
        dydtheta = np.zeros_like(theta_2D)
        dzdtheta = np.zeros_like(theta_2D)
        dxdzeta = np.zeros_like(theta_2D)
        dydzeta = np.zeros_like(theta_2D)
        dzdzeta = np.zeros_like(theta_2D)

        for i in range(mnmax_nescin):
            angle = xm_nescin[i] * theta_2D + xn_nescin[i] * zetal_2D * nfp
            angle2 = zetal_2D

            x += rmnc_nescin[i] * np.cos(angle) * np.cos(angle2)
            y += rmnc_nescin[i] * np.cos(angle) * np.sin(angle2)
            z += zmns_nescin[i] * np.sin(angle)

            for j in range(coilsPerHalfPeriod * numHalfPeriodsToPlot):
                angle = xm_nescin[i] * contours_theta[j] + xn_nescin[i] * contours_zeta[j] * nfp
                angle2 = contours_zeta[j]

                contours_x[j] += rmnc_nescin[i] * np.cos(angle) * np.cos(angle2)
                contours_y[j] += rmnc_nescin[i] * np.cos(angle) * np.sin(angle2)
                contours_z[j] += zmns_nescin[i] * np.sin(angle)

                contours_dxdtheta[j] -= xm_nescin[i] * rmnc_nescin[i] * np.sin(angle) * np.cos(angle2)
                contours_dydtheta[j] -= xm_nescin[i] * rmnc_nescin[i] * np.sin(angle) * np.sin(angle2)
                contours_dzdtheta[j] += xm_nescin[i] * zmns_nescin[i] * np.cos(angle)

                contours_dxdzeta[j] -= nfp * xn_nescin[i] * rmnc_nescin[i] * np.sin(angle) * np.cos(angle2) - \
                                       rmnc_nescin[i] * np.cos(angle) * np.sin(angle2)
                contours_dydzeta[j] -= nfp * xn_nescin[i] * rmnc_nescin[i] * np.sin(angle) * np.sin(angle2) + \
                                       rmnc_nescin[i] * np.cos(angle) * np.cos(angle2)
                contours_dzdzeta[j] += nfp * xn_nescin[i] * zmns_nescin[i] * np.cos(angle)

        for j in range(coilsPerHalfPeriod * numHalfPeriodsToPlot):
            Nx = contours_dydzeta[j] * contours_dzdtheta[j] - contours_dzdzeta[j] * contours_dydtheta[j]
            Ny = contours_dzdzeta[j] * contours_dxdtheta[j] - contours_dxdzeta[j] * contours_dzdtheta[j]
            Nz = contours_dxdzeta[j] * contours_dydtheta[j] - contours_dydzeta[j] * contours_dxdtheta[j]
            norm_normal = np.sqrt(Nx * Nx + Ny * Ny + Nz * Nz)
            Nx /= norm_normal
            Ny /= norm_normal
            Nz /= norm_normal

            indices = np.arange(contours_x[j].size)
            next_index = np.roll(indices, -1)
            prev_index = np.roll(indices, 1)
            Tx = contours_x[j][next_index] - contours_x[j][prev_index]
            Ty = contours_y[j][next_index] - contours_y[j][prev_index]
            Tz = contours_z[j][next_index] - contours_z[j][prev_index]
            norm_tangent = np.sqrt(Tx * Tx + Ty * Ty + Tz * Tz)
            Tx /= norm_tangent
            Ty /= norm_tangent
            Tz /= norm_tangent

            Bx = Ty * Nz - Tz * Ny
            By = Tz * Nx - Tx * Nz
            Bz = Tx * Ny - Ty * Nx

            coils_x1 = (contours_x[j] + coil_thickness * (Nx + Bx))
            coils_x2 = (contours_x[j] + coil_thickness * (Nx - Bx))
            coils_x3 = (contours_x[j] + coil_thickness * (-Nx - Bx))
            coils_x4 = (contours_x[j] + coil_thickness * ((-Nx + Bx)))
            coils_x_ar = np.vstack((coils_x1, coils_x2))
            coils_x_ar = np.vstack((coils_x_ar, coils_x3))
            coils_x_ar = np.vstack((coils_x_ar, coils_x4))

            coils_y1 = (contours_y[j] + coil_thickness * (Ny + By))
            coils_y2 = (contours_y[j] + coil_thickness * (Ny - By))
            coils_y3 = (contours_y[j] + coil_thickness * (-Ny - By))
            coils_y4 = (contours_y[j] + coil_thickness * ((-Ny + By)))
            coils_y_ar = np.vstack((coils_y1, coils_y2))
            coils_y_ar = np.vstack((coils_y_ar, coils_y3))
            coils_y_ar = np.vstack((coils_y_ar, coils_y4))

            coils_z1 = (contours_z[j] + coil_thickness * (Nz + Bz))
            coils_z2 = (contours_z[j] + coil_thickness * (Nz - Bz))
            coils_z3 = (contours_z[j] + coil_thickness * (-Nz - Bz))
            coils_z4 = (contours_z[j] + coil_thickness * ((-Nz + Bz)))
            coils_z_ar = np.vstack((coils_z1, coils_z2))
            coils_z_ar = np.vstack((coils_z_ar, coils_z3))
            coils_z_ar = np.vstack((coils_z_ar, coils_z4))

            coils_x.append(coils_x_ar)
            coils_y.append(coils_y_ar)
            coils_z.append(coils_z_ar)

        for j in range(coilsPerHalfPeriod * numHalfPeriodsToPlot):
            nextColor = (j - 1) % colors.shape[0]
            for k in range(4):
                # Generate full paths for files inside "coords" directory
                centre = os.path.join("coords", f"c_{j}.csv")
                xfile = os.path.join("coords", f"x_{j + 1}_{k + 1}.csv")
                yfile = os.path.join("coords", f"y_{j + 1}_{k + 1}.csv")
                zfile = os.path.join("coords", f"z_{j + 1}_{k + 1}.csv")
                max_count = coils_x[j].shape[1]

                # Open the files using the full paths
                with open(yfile, 'w') as fileIDy, open(xfile, 'w') as fileIDx, open(zfile, 'w') as fileIDz, open(centre,
                                                                                                                 'w') as fileIDc:
                    for l in range(max_count):
                        fileIDx.write(f"{coils_x[j][k, l]}\n")
                        fileIDy.write(f"{coils_y[j][k, l]}\n")
                        fileIDz.write(f"{coils_z[j][k, l]}\n")
                        fileIDc.write(f"{contours_x[j][l]} {contours_y[j][l]} {contours_z[j][l]}\n")

    return ()


parser = argparse.ArgumentParser(description="Generate coil coordinates from regcoil")
parser.add_argument("--regcoil_path", type=str, required=True, help="Path to regcoil output")
parser.add_argument("--nescin_path", type=str, required=True, help="Path to nescin output")
parser.add_argument("--coils_per_p", type=int, required=True, help="Coils per period")
parser.add_argument("--p", type=int, required=True, help="stellarator periodicity")
parser.add_argument("--c_t", type=float, required=True, help="Coil thickness")
args = parser.parse_args()

coil_coord_gen(args.regcoil_path, args.nescin_path, args.coils_per_p, args.p, args.c_t)



