# Code to generate coils as individual geo/step files - better for Alex's costing
import gmsh
import sys

import argparse
import numpy as np
import matplotlib.pyplot as plt
import csv
import time
import zipfile
import os


# Create geo file
def make_coils(coil_max):
    # Read in coordinates
    # fy = open("y.csv", "r")
    # fz = open("z.csv", "r")

    coil_start = 1
    coil_num = coil_start

    k = 1  # number of loops defining the surfaces
    point_count = 0
    line_count = 0

    # points per curve
    ppc = 3

    curve_init = np.zeros(coil_max)
    curve_final = np.zeros(coil_max)

    line_max_array = np.zeros(coil_max + 1)

    #    coil_max=12

    while coil_num <= coil_max:

        print("current coil: ", coil_num, coil_max)

        gmsh.initialize()
        #    gmsh.fltk.initialize()
        gmsh.option.setNumber("General.NumThreads", 16)
        gmsh.option.setNumber("General.Terminal", 1)
        gmsh.model.add("stell_layers")
        gmsh.option.setString("Geometry.OCCTargetUnit", "M")

        point_count = 0
        line_count = 0
        spline_list = ""
        spline_count = 0

        k = 1

        while k <= 4:

            spline_count = 0

            count = 0
            x1_str = []
            y1_str = []
            z1_str = []

            filex = "coords/x_" + str(coil_num) + "_" + str(k) + ".csv"
            filey = "coords/y_" + str(coil_num) + "_" + str(k) + ".csv"
            filez = "coords/z_" + str(coil_num) + "_" + str(k) + ".csv"

            # print(coil_num)
            #  print(filex)

            with open(filex, "r") as file:

                for item in file:
                    count = count + 1
                    # print(item)
                    x1_str.append(item)

                # print(count,x1_str)
                tot_point = count

            tot_point = tot_point - 1
            # print("Coil:",coil_num,"points",tot_point)

            if ((tot_point - ppc) % (ppc - 1) == 0):
                curve_jump = (int((tot_point - ppc) / (ppc - 1))) + 1
            else:
                curve_jump = (int((tot_point - ppc) / (ppc - 1))) + 2
            #  print("Curve jump: ", curve_jump)

            with open(filey, "r") as file:

                for item in file:
                    # count=count+1
                    # print(item)
                    y1_str.append(item)

            # print(count,x1_str)
            # tot_point=count

            with open(filez, "r") as file:

                for item in file:
                    #  count=count+1
                    # print(item)
                    z1_str.append(item)

                # print(count,x1_str)
                # tot_point=count
                # Check point spacing:
                count = 1
                counter = 1
                rem_counter = 0
                while counter <= tot_point - 1:
                    #                   print(counter)
                    #                   print(count)

                    x1 = float(x1_str[count])
                    y1 = float(y1_str[count])
                    z1 = float(z1_str[count])

                    x2 = float(x1_str[count - 1])
                    y2 = float(y1_str[count - 1])
                    z2 = float(z1_str[count - 1])

                    dist = (((x2 - x1) ** 2) + ((y2 - y1) ** 2) + ((z2 - z1) ** 2)) ** (0.5)

                    if dist < 0.00:
                        rem_counter = rem_counter + 1
                        del x1_str[count]
                        del y1_str[count]
                        del z1_str[count]
                    #             print(x1,x2,y1,y2,z1,z2,dist)
                    #                       print(count)
                    else:
                        count = count + 1
                    counter = counter + 1

                #            print("points to remove:", rem_counter)
                tot_point = tot_point - rem_counter
                #           print("Coil:",coil_num,"points",tot_point)

                if ((tot_point - ppc) % (ppc - 1) == 0):
                    curve_jump = (int((tot_point - ppc) / (ppc - 1))) + 1
                else:
                    curve_jump = (int((tot_point - ppc) / (ppc - 1))) + 2
                #          print("Curve jump: ", curve_jump)

                x = np.zeros(tot_point)
                y = np.zeros(tot_point)
                z = np.zeros(tot_point)
                count = 0
                #  print("tot_point",tot_point)
                # convert to correct type (integer/float) and create complete loop

                while count <= tot_point:

                    if count <= tot_point - 1:
                        x[count] = float(x1_str[count])
                        y[count] = float(y1_str[count])
                        z[count] = float(z1_str[count])

                    # REORDER POINTS AS NECESSARY

                    # count=0

                    if count <= tot_point - 1:
                        # print(count,x[count],y[count],z[count])
                        point_count = point_count + 1
                        #                        print("coil:",coil_num, "point:",point_count)
                        #    print("Point(",point_count,") = {",x[count],",",y[count],",",z[count],", 1.0};",file=geo)
                        gmsh.model.occ.addPoint(x[count], y[count], z[count], 1.0, point_count)
                        line_num = point_count - 1

                        if count == 0:
                            # print("NEW SURFACE LOOP")
                            # Remember start point of loop
                            #                            line_count=line_count+1
                            spline_count = spline_count + 1
                            spline_list = "" + str(point_count) + ","
                            start_point = point_count
                            spline_l = []
                            spline_l.append(point_count)
                        elif count == tot_point - 1:
                            # Connect to previous point
                            #                            line_count=line_count+1
                            spline_list = spline_list + str(point_count) + "," + str(start_point)
                            spline_l.append(point_count)
                            spline_l.append(start_point)
                            line_count = line_count + 1
                            spline_count = spline_count + 1
                            # print("Spline(",line_count,") = {",spline_list,"};",file=geo)
                            gmsh.model.occ.addSpline(spline_l, line_count)
                        #                           print("Line(",line_count,") = {",point_count-1,",",point_count,"};",file=geo)

                        # Connect to start point
                        #                            line_count=line_count+1
                        #                            print("Spine(",line_count,") = {",point_count,",",start_point,"};",file=geo)
                        #                            print('//+',file=geo)
                        # print(tot_point,line_num+1)
                        else:
                            # Connect to previous point
                            #                            line_count=line_count+1
                            spline_count = spline_count + 1
                            #                            print("Line(",line_count,") = {",point_count-1,",",point_count,"};",file=geo)
                            if (spline_count % ppc == 0):
                                spline_list = spline_list + str(point_count)
                                spline_l.append(point_count)
                                line_count = line_count + 1
                                gmsh.model.occ.addSpline(spline_l, line_count)
                                #      print("Spline(",line_count,") = {",spline_list,"};",file=geo)
                                #    print('//+',file=geo)
                                spline_list = "" + str(point_count) + ","
                                spline_l = []
                                spline_l.append(point_count)
                        #                                spline_count=1

                        # Connect points to other surfaces
                        # If k=4 all other surface loops identified
                        if k == 4:

                            l = 3
                            if (((point_count - ((3 * (tot_point))) - 1) % (ppc - 1) == 0) or (
                            (point_count == (1 + (3 * tot_point))))):
                                while l >= 0:
                                    # print(l)

                                    if ((point_count == (1 + (3 * tot_point)))):
                                        print(point_count)

                                    if l == 0:
                                        line_count = line_count + 1
                                        gmsh.model.occ.addLine((point_count - ((l) * (tot_point))),
                                                               (point_count - ((3 * (tot_point)))), line_count)
                                        #                                        print("Line(",line_count,") = {",(point_count-((l)*(tot_point))),",",(point_count-((3*(tot_point)))),"};",file=geo)
                                        #                                        print('//+',file=geo)
                                        # print(line_count,(point_count-((l)*(tot_point-1))),(point_count-((3*(tot_point-1)))))
                                        l = l - 1

                                    else:
                                        line_count = line_count + 1
                                        gmsh.model.occ.addLine((point_count - ((l) * (tot_point))),
                                                               (point_count - ((l - 1) * (tot_point))), line_count)
                                        #                                        print("Line(",line_count,") = {",(point_count-((l)*(tot_point))),",",(point_count-((l-1)*(tot_point))),"};",file=geo)
                                        #                                       print('//+',file=geo)
                                        # print(line_count,(point_count-((l)*(tot_point-1))),(point_count-((l-1)*(tot_point-1))))
                                        l = l - 1

                    # With all lines added, can now set the surfaces
                    # print(point_count)
                    if (spline_count % ppc == 0):
                        spline_count = 1
                    count = count + 1
            line_max_array[coil_num] = line_count
            # Step above complete, now set surfaces and volumes

            # print("K:",k)
            if k == 4:

                count_2 = int(0) + 1
                curve_num = 1

                while count_2 <= curve_jump:

                    r1 = count_2

                    r3 = -(count_2 + curve_jump)
                    r4 = -(count_2 + (3 * curve_jump) + ((count_2 - 1) * k))

                    t1 = count_2

                    t3 = -(count_2 + ((3 * curve_jump) + (count_2) * k))
                    t4 = (count_2 + ((3 * curve_jump) + (count_2) * k) - 1)

                    l1 = (count_2 + ((3 * curve_jump) + (count_2) * k))

                    l3 = -(count_2 + ((2 * curve_jump)))
                    l4 = (count_2 + ((3 * curve_jump) + (count_2) * k) - 2)

                    b1 = (count_2 + (1 * curve_jump))

                    b3 = -(count_2 + ((2 * curve_jump)))
                    b4 = -(count_2 + (3 * curve_jump) + ((count_2) * k) - 3)

                    if count_2 == curve_jump:
                        r2 = (1 + (3 * curve_jump))
                        t2 = -(1 + (3 * curve_jump) + ((1) * k) - 1)
                        l2 = -(1 + ((3 * curve_jump) + (1) * k) - 2)
                        b2 = (1 + (3 * curve_jump) + ((1) * k) - 3)

                    else:

                        r2 = (count_2 + (3 * curve_jump) + ((count_2) * k) + 1)
                        t2 = -(count_2 + ((3 * curve_jump) + (count_2 + 1) * k))
                        l2 = -(count_2 + ((3 * curve_jump) + (count_2) * k) + (k - 1))
                        b2 = (count_2 + (3 * curve_jump) + ((count_2 + 1) * k) - 2)

                    gmsh.model.occ.addCurveLoop([r1, r2, r3, r4], curve_num)
                    gmsh.model.occ.addSurfaceFilling(curve_num, curve_num)

                    #  print("Curve Loop(",curve_num,")= {",r1,",",r2,",",r3,",",r4,"};",file=geo)
                    #  print("//+",file=geo)
                    #  print("Surface(",curve_num,") = {",curve_num,"};",file=geo)
                    #  print("//+",file=geo)

                    curve_num = curve_num + 2

                    gmsh.model.occ.addCurveLoop([t1, t2, t3, t4], curve_num)
                    gmsh.model.occ.addSurfaceFilling(curve_num, curve_num)

                    #     print("Curve Loop(",curve_num,")= {",t1,",",t2,",",t3,",",t4,"};",file=geo)
                    #    print("//+",file=geo)
                    #   print("Surface(",curve_num,") = {",curve_num,"};",file=geo)
                    #  print("//+",file=geo)

                    curve_num = curve_num + 2

                    gmsh.model.occ.addCurveLoop([l1, l2, l3, l4], curve_num)
                    gmsh.model.occ.addSurfaceFilling(curve_num, curve_num)

                    #     print("Curve Loop(",curve_num,")= {",l1,",",l2,",",l3,",",l4,"};",file=geo)
                    #    print("//+",file=geo)
                    #   print("Surface(",curve_num,") = {",curve_num,"};",file=geo)
                    #  print("//+",file=geo)

                    curve_num = curve_num + 2

                    gmsh.model.occ.addCurveLoop([b1, b2, b3, b4], curve_num)
                    gmsh.model.occ.addSurfaceFilling(curve_num, curve_num)

                    #              print("Curve Loop(",curve_num,")= {",b1,",",b2,",",b3,",",b4,"};",file=geo)
                    #             print("//+",file=geo)
                    #            print("Surface(",curve_num,") = {",curve_num,"};",file=geo)
                    #           print("//+",file=geo)
                    curve_num = curve_num + 2
                    #       b1=count_2+(1*(tot_point-1))
                    #      b2=count_2+(3*(tot_point-1)+6)
                    #     b3=(count_2+(2*(tot_point-1)))
                    #    b4=(count_2+(3*(tot_point-1)+1))
                    count_2 = count_2 + 1

            k = k + 1
        gmsh.model.occ.synchronize()
        # gmsh.fltk.run()
        #  print(coil_num,curve_init,final_curve)

        # SET VOLUME
        #        print("//+",file=geo)
        #   print("Coherence;",file=geo)
        #     print('//+',file=geo)

        count_3 = 1
        sl_num = 1
        string_sl = "Surface Loop(" + str(sl_num) + ")= {"
        list_sl = []

        while count_3 <= (4 * curve_jump):

            if count_3 == 4 * curve_jump:

                string_sl = string_sl + str(int(((2 * count_3) - 1))) + "};"
                list_sl.append((int(((2 * count_3) - 1))))
                count_3 = count_3 + 1
                #  print(string_sl,file=geo)
                sl_c = gmsh.model.occ.addSurfaceLoop(list_sl, sl_num)
                #   print("//+",file=geo)
                gmsh.model.occ.addVolume([sl_num], sl_num)
                gmsh.model.occ.synchronize()
                # gmsh.fltk.run()
            #   print("Volume(",sl_num,") = {", sl_num,"};",file=geo)
            #   print("//+",file=geo)

            else:

                string_sl = string_sl + str(int(((2 * count_3) - 1))) + ", "
                list_sl.append((int(((2 * count_3) - 1))))
                count_3 = count_3 + 1

        # COIL DEFINED EXPORT STEP FILE
        gmsh.model.mesh.generate(3)
        coil_name = "S_coil_" + str(coil_num) + ".step"
        gmsh.write(coil_name)

        coil_num = coil_num + 1
        # Remove previous coil geom
        # gmsh.model.removeEntities([(3,sl_num)], recursive=True)

        # gmsh.fltk.run()
        gmsh.finalize()


# Function to zip .step files
def zip_step_files():
    # Define the name of the zip file
    zip_filename = "cad_files.zip"

    # Create a ZipFile object
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        # Loop through all files in the current directory
        for root, dirs, files in os.walk("."):
            for file in files:
                # Check if the file ends with .step
                if file.endswith(".step"):
                    # Add the file to the zip archive
                    zipf.write(os.path.join(root, file), arcname=file)
                    print(f"Zipping file: {file}")

    print(f"All .step files zipped into {zip_filename}")


parser = argparse.ArgumentParser(description="Generate geo files for the coils.")
parser.add_argument("--coils_per_p", type=int, required=True, help="Number of coils per period")
parser.add_argument("--p", type=int, required=True, help="Number of periods")
args = parser.parse_args()
# Now call your function with the parsed arguments
coils_per_p = args.coils_per_p
period = args.p
coils_total = period * coils_per_p
make_coils(coils_total)
# Call the function after generating the coil .step files
zip_step_files()
