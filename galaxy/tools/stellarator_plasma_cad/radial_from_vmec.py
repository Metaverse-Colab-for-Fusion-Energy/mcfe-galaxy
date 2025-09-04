#Create radial build of stellarator from an existing VMEC input file 
import gmsh
import csv
import numpy as np

from matplotlib.patches import Ellipse
import matplotlib.transforms as transforms

def make_build(input_file,Nphi,Ntheta,thickness_list,mag_ax,b_type,m):
 
    print("Nphi,Ntheta: ",Nphi,Ntheta)

    gmsh.initialize()
#    gmsh.fltk.initialize()
    gmsh.option.setNumber("General.NumThreads",16)
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.model.add("stell_layers")
    gmsh.option.setString("Geometry.OCCTargetUnit", "M")

    Coords = np.zeros((Nphi+1,Ntheta+1,3))
    Coords_orig = np.zeros((Nphi+1,Ntheta+1,3))
    X = np.zeros((Nphi+1,Ntheta+1))
    Y = np.zeros((Nphi+1,Ntheta+1))
    Z = np.zeros((Nphi+1,Ntheta+1))
#    mag_ax = np.zeros((Nphi+1,3))
    #Read in 3D coords file  
    X_str = []
    Y_str = []
    Z_str = [] 

    counter = 0

    tot_layer = len(thickness_list)

    point_file = open(input_file, "r")
    file = csv.DictReader(point_file)

    for col in file:
    # count number of coils
        counter = counter + 1

    # Read in values
        X_str.append(col["X"])
        Y_str.append(col["Y"])
        Z_str.append(col["Z"])

    tot_point = counter

    counter=0
    Phi_count=0
  
    while Phi_count <= Nphi: 

        Theta_count = 0

        while Theta_count <=Ntheta:

            Coords_orig[Phi_count,Theta_count,0] = X_str[counter] 
            Coords_orig[Phi_count,Theta_count,1] = Y_str[counter] 
            Coords_orig[Phi_count,Theta_count,2] = Z_str[counter]

#            if Phi_count ==0: 
#                print(Phi_count,Theta_count,Coords_orig[Phi_count,Theta_count,0]) 
   
            counter=counter+1
            Theta_count = Theta_count+1

        Phi_count=Phi_count+1
    #Calculate average R0 
    half_loop = int((0.5*Ntheta))+1
    R0 = (Coords_orig[0,0,0] - (0.5*(Coords_orig[0,0,0] - Coords_orig[0,int((0.5*Ntheta))+1,0])))
 #   print(Coords_orig[0,0,0],Coords_orig[0,46,0])
    print("R0 estimate: ",R0)

    dPhi = (2*np.pi)/Nphi
    Phi=0.0 
    Phi_count = 0 

    centre_name= "central_loop.csv"
    centre = open(centre_name, "w")

    layer_count =0 
    sum_thickness=0.0

    
    if layer_count > 0: 
        b_prev = b_prev+thickness

    while layer_count <=0: 

        P=0.0 
        Phi_count = 0
        thickness = thickness_list[layer_count] 
        plasma_thickness = thickness_list[0] 
        sum_thickness = sum_thickness + thickness
        print("layer: ", layer_count, "thickness of layer:",thickness)


        while Phi_count<= Nphi : 

            T = 0.0 
            Theta_count=0

            while Theta_count <=Ntheta:
       
            # If layer =0, plasma keep same as VMEC boundary coords 
                if layer_count == 0: 
                    Coords[Phi_count,Theta_count,0]=Coords_orig[Phi_count,Theta_count,0]
                    Coords[Phi_count,Theta_count,1]=Coords_orig[Phi_count,Theta_count,1]
                    Coords[Phi_count,Theta_count,2]=Coords_orig[Phi_count,Theta_count,2]


                  #  print(Coords[Phi_count,Theta_count,0],              
                Theta_count = Theta_count + 1 
#            P = P + dphi
            Phi_count=Phi_count+1

        #All points determined - make geo file 

        #Write coordinates to a file:

        phi_test=0 

        while phi_test <= Nphi:

            theta_test=0 
            while theta_test <=Ntheta: 

                dist = np.sqrt(((Coords_orig[phi_test,theta_test,0] - Coords[phi_test,theta_test,0])**2) + ((Coords_orig[phi_test,theta_test,1] - Coords[phi_test,theta_test,1])**2) + ((Coords_orig[phi_test,theta_test,2] - Coords[phi_test,theta_test,2])**2))
                
                theta_test=theta_test+1 
            phi_test=phi_test+1
        

        # Reorder loops and remove overlapping points
        loop_jump = Ntheta +1 
        # Last loop is a repeat of the first, ignore
        loop_num_tot = Nphi
        # loop_num_tot = 5
        loop_num = 1
        final_point=(int(((loop_num_tot - 1) * (loop_jump-1))) + loop_jump-2)
        #print("FINAL POINT:",final_point)

        # Define array to store coordinates for each loop

        while loop_num <= loop_num_tot:
  #  print("Loop number: ", loop_num)
            count_min = int(((loop_num - 1) * loop_jump) -(1*(loop_num-1)))
            count_max = count_min + loop_jump-1
            count = count_min
            #filename2 = "NEW_RUN/layer_" + str(layer_count) + "_loop_" +str(loop_num) + ".csv"
           # output_file = open(filename2, "w")
          #  print("Count max: ", count_max)

            while count <= count_max-1:
                point_num = count - count_min
                #print("POINT NUM:,",point_num,count)


                gmsh.model.occ.addPoint(
                    Coords[loop_num-1,point_num,  0],
                    Coords[ loop_num-1,point_num, 1],
                    Coords[ loop_num-1,point_num, 2],
                    1.0,
                    count,
                )


         #       if (count%(Ntheta/16))==0:
          #          print(
           #             "Point(",
            #            count,
             #           ") = {",
              #          Coords[loop_num-1,point_num,  0],
               #         ",",
                #        Coords[ loop_num-1,point_num, 1],
                 #       ",",
                  #      Coords[ loop_num-1,point_num, 2],
                   #     ",",
                    #    "1.0};",
                     #   file=geo2,
             #       )
              #      print("//+", file=geo2)

                count = count + 1

            loop_num = loop_num + 1

        # Send lines to GMSH
# loop_num_tot = 10
        loop_num = 1
        loop_max = loop_num_tot

        line_shift = Ntheta*Nphi

        while loop_num <= loop_num_tot:
            count_min = int(((loop_num - 1) * loop_jump) -(1*(loop_num-1)))
            count_max = count_min + loop_jump-1
          #  print("count_max : " , count_max)
            count = count_min

            while count <= count_max-1:
                point_num = count - count_min

        # Connect points of the loop
                if count == count_max-1:
            # print("Line(",count,") = {",count,",",point_num,"};",file=geo)
            # print('//+',file=geo)
               #     print(count)

                    gmsh.model.occ.addLine (count,count - (loop_jump - 2),count)



                else:

                    gmsh.model.occ.addLine (count,count +1,count)

        # Final loop must connect back to the first

                if loop_num == loop_num_tot:
  
                    gmsh.model.occ.addLine (count,point_num,count+line_shift)

                else:
                    gmsh.model.occ.addLine (count,count + loop_jump-1,count+line_shift)

                count = count + 1

            loop_num = loop_num + 1

        #ADD SURFACES
        loop_num = 1

# line_shift = tot_point
#print(line_shift)
        sloop_str = "Surface Loop(1) = {"
        sloop_list = [] 


        while loop_num <= loop_num_tot:
    #  if loop_num == loop_num_tot:
    #     loop_num = loop_max
    #    print("loop max =, ",loop_max)
    #   loop_num_tot = loop_max

            count_min = int(((loop_num - 1) * loop_jump) -(1*(loop_num-1)))
            count_max = count_min + loop_jump-2
          #  print("Surface count max: ",count_max)
            count = count_min

            while count <= count_max:
                point_num = count - count_min

                if count == count_max:
                    if loop_num == loop_num_tot:
                       # print("FINAL LOOP")


                        gmsh.model.occ.addCurveLoop([ count,count + line_shift,point_num,(-1 * (line_shift + count - point_num))],((2 * count) + 1))
                        gmsh.model.occ.addSurfaceFilling(((2 * count) + 1),count)

                    else:

                        gmsh.model.occ.addCurveLoop([ count,count + line_shift,count_max + point_num+1,(-1 * (line_shift + count - point_num))],((2 * count) + 1))
                        gmsh.model.occ.addSurfaceFilling(((2 * count) + 1),count)
                        

            # print(count,(2*count)+1,(-1*(line_shift+count-point_num)))

                else:
                    if loop_num == loop_num_tot:

                        gmsh.model.occ.addCurveLoop([ count,count + line_shift,point_num,(-1 * (count + line_shift + 1))],((2 * count) + 1))
                        gmsh.model.occ.addSurfaceFilling(((2 * count) + 1),count)


                    else:

                        gmsh.model.occ.addCurveLoop([ count,count + line_shift,count_max + point_num+1,(-1 * (count + line_shift + 1))],((2 * count) + 1))
                        gmsh.model.occ.addSurfaceFilling(((2 * count) + 1),count)

            # Add surface to surface loop
                if count == final_point:
                    sloop_str = sloop_str + str(count) + "};"
                    sloop_list.append(count)

                    gmsh.model.occ.addSurfaceLoop(sloop_list,layer_count+1)
                    gmsh.model.occ.addVolume([layer_count+1],layer_count+1)

                else:
                    sloop_list.append(count)

                count = count + 1

            loop_num = loop_num + 1

        gmsh.model.occ.synchronize()
        # gmsh.fltk.run()
        gmsh.model.mesh.generate(3)
        step_name = "layer_"+ str(layer_count)+".step"
        gmsh.write(step_name)        

        #print(Coords)
        layer_count=layer_count+1 


    return()





#make_stellarator(5.0,3,a_vals,b_vals)

# Set up the argument parser
#parser = argparse.ArgumentParser(description="Plot a stellarator configuration from VMEC file.")
#parser.add_argument("--file_in", type=str, required=True, help="Name of input file")
#parser.add_argument("--nP", type=int, required=True, help="Number of Phi values in 2 pi")
#parser.add_argument("--nT", type=int, required=True, help="Number of theta values in 2 pi")
#parser.add_argument("--t_list", type=str, required=True, help="Thicknesses of the layers")

# Parse the arguments
#args = parser.parse_args()
#
#thicknesses = list(map(float, args.t_list.strip('[]').split(',')))

#Call VMEC boundary to 3D coord convertor

# Now call your function with the parsed arguments
#make_build(args.file_in,args.nP,args.nT,thicknesses)
