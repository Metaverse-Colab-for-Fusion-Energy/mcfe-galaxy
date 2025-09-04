import numpy as np
from pylab import *
import csv
import re


def MAG_AX(filepath,Nphi,axis_array):

    dphi=(2*np.pi)/Nphi

    #Read modified VMEC input file
    file1 = open(filepath, "r")

    Rax_str =""
    Zax_str =""
    fp = 3
    RAXIS_LIST =False
    ZAXIS_LIST =False

    for line in file1.readlines():           
       # print(line)
        if line.startswith('  RAXIS ='):
            RAXIS_LIST =True 

        if line.startswith('  ZAXIS ='):
            RAXIS_LIST =False
            ZAXIS_LIST =True

        if line.startswith('  R'):
            ZAXIS_LIST =False

        if RAXIS_LIST ==True: 
        #Add line to string 

            Rax_str=Rax_str + line

        if ZAXIS_LIST ==True: 
        #Add line to string 

            Zax_str=Zax_str + line

    
    file1.close()
    Rax_str=re.sub("[^0-9 . E + -]","",Rax_str)
    Zax_str=re.sub("[^0-9 . E + -]","",Zax_str)
  
    Rax_list = Rax_str.split()
    Zax_list = Zax_str.split() 

    print("AXIS LIST:")
    print(Rax_list) 
    print(Zax_list)

#    print(Rax_list)
#    print(Zax_list)

    Rax_count = len(Rax_list)
    Rax = np.zeros(Rax_count)
    Zax = np.zeros(Rax_count)

  
    
    count = 0
    
    while count <= Rax_count-1: 
        Rax[count] = float(Rax_list[count])  
        Zax[count] = float(Zax_list[count])       
#        print(Rax[count],Zax[count])
        count = count+1

   #Calculate R,Z values
    n_count = 0 
    phi_count = 0 
    phi = 0.0

    Rax_fin = np.zeros(Nphi+1)
    Zax_fin = np.zeros(Nphi+1)
    xax= np.zeros(Nphi+1)
    yax= np.zeros(Nphi+1)

    RZ_file = open("MagAxis_RZ.csv", "w")
    file_3D = open("MagAxis_3D.csv", "w")

    while phi_count <= Nphi: 

        n_count=0
        
        while n_count <= Rax_count-1:

            Rax_fin[phi_count] = Rax_fin[phi_count] + (Rax[n_count]*(np.cos(-1*fp*(n_count)*phi)))
            Zax_fin[phi_count] = Zax_fin[phi_count] + (Zax[n_count]*(np.sin(-1*fp*(n_count)*phi)))
            n_count=n_count+1

        print(Rax_fin[phi_count],",",Zax_fin[phi_count],file=RZ_file)

        #Calculate in 3D coords
        xax[phi_count] = Rax_fin[phi_count] * np.cos(phi)
        yax[phi_count] = Rax_fin[phi_count] * np.sin(phi)
        axis_array[phi_count,0] = xax[phi_count]
        axis_array[phi_count,1] = yax[phi_count]
        axis_array[phi_count,2] = Zax_fin[phi_count]

#        print(xax[phi_count],",",yax[phi_count],",",Zax_fin[phi_count],file=file_3D)
        print(axis_array[phi_count,0],",",axis_array[phi_count,1],",",axis_array[phi_count,2],file=file_3D)

        phi=phi+dphi 
        phi_count=phi_count+1

    return(axis_array)

#array1 = np.zeros((91,3))
#MAG_AX("input.ncsx_c09r00_fixed",90,array1)
#print(array1)

def VMEC_RBC_ZBS(filepath): 

    #Read modified VMEC input file
    file1 = open(filepath, "r")
    file2 = open("rz_coords.csv", "w")
    print("n,m,RBC,ZBS",file=file2)

    RBC_str =""
    ZBS_str =""
    R_LIST =False
    Z_LIST =False
 

    for line in file1.readlines():           
       # print(line)
        if "RBC" in line:
            print("RBC FOUND!")
            print(line) 
            line_str = re.sub('[^0-9, . E + -]','',line)
            print(line_str)
            line_str=line_str.replace(',', ' ')
            line_l=line_str.split()
            print(line_l)

            for i in range(len(line_l)): 
                print(i,line_l[i])

            n = int(line_l[0])
            m = int(line_l[1])
            RBC=float(line_l[2])
            ZBS=float(line_l[5]) 
 
            print(n,m,RBC,ZBS,sep=",",file=file2)
  
    file1.close()

    return() 


def VMEC_TO_RZ(filepath,Ntheta,Nphi,fp,plasma_3D):

    #Read modified VMEC input file
    file1 = open(filepath, "r")

    file = csv.DictReader(file1)

    n_str =[]
    m_str =[]
    rbc_str = []
    zbs_str = []

    count = 0

    for col in file:
        # Read in values from vessel file
        n_str.append(col["n"])
        m_str.append(col["m"])
        rbc_str.append(col["RBC"])
        zbs_str.append(col["ZBS"])
        count = count + 1

   # Create correct size arrays to store coords
    tot_point = count

    n = np.zeros(tot_point)
    m = np.zeros(tot_point)
    rbc = np.zeros(tot_point)
    zbs = np.zeros(tot_point)

    count=0

    while count <= tot_point-1:
        n[count] = int(n_str[count]) 
        m[count] = int(m_str[count])
        rbc[count] = float(rbc_str[count])
        zbs[count] = float(zbs_str[count])
        count=count+1   

    # Set theta, phi values 
    dtheta = (2 * np.pi) / Ntheta
    dphi = (2 * np.pi) / Nphi
    filename3 = "3D_total.csv"
    output3D = open(filename3, "w")
    print("X,Y,Z",file=output3D)
    outputRZ = open("RZ_total.csv", "w")
    print("R,Z",file=outputRZ)

    phi_num = 0
    phi=0.0
    while phi_num <= Nphi:



        theta = 0.0
        theta_num = 0
        while theta_num <=Ntheta:

            R_sum =0.0 
            Z_sum = 0.0 
            count = 0

            while count <= tot_point-1:             
                R_sum = R_sum + (rbc[count])*(np.cos((m[count]*theta) - (n[count]*fp*phi)))
                Z_sum = Z_sum + (zbs[count])*(np.sin((m[count]*theta) - (n[count]*fp*phi)))
                count = count+1
          #Create coordinate file of different theta vals for same phi
            x = R_sum * np.cos(phi)
            y = R_sum * np.sin(phi)

            plasma_3D[phi_num,theta_num,0] = x 
            plasma_3D[phi_num,theta_num,1] = y 
            plasma_3D[phi_num,theta_num,2] = Z_sum 

            theta = theta + dtheta
            theta_num = theta_num + 1

            print(x,",",y,",",Z_sum,file=output3D) # Write 3D cartesian coords to file 
            print(R_sum,",",Z_sum,file=outputRZ) #Write R,Z coords to file

        phi = phi + dphi
        phi_num = phi_num + 1

    print("Coordinates converted from VMEC to RZ and 3D") 
    return (plasma_3D)
     
 

def VMEC_TO_RZ_orig(filepath,Ntheta,Nphi,fp,plasma_3D):

    #Read modified VMEC input file
    file1 = open(filepath, "r")

    file = csv.DictReader(file1)

    n_str =[]
    m_str =[]
    rbc_str = []
    zbs_str = []

    count = 0

    for col in file:
        # Read in values from vessel file
        n_str.append(col["n"])
        m_str.append(col["m"])
        rbc_str.append(col["RBC"])
        zbs_str.append(col["ZBS"])
        count = count + 1

   # Create correct size arrays to store coords
    tot_point = count

    n = np.zeros(tot_point)
    m = np.zeros(tot_point)
    rbc = np.zeros(tot_point)
    zbs = np.zeros(tot_point)

    count=0

    while count <= tot_point-1:
        n[count] = int(n_str[count]) 
        m[count] = int(m_str[count])
        rbc[count] = float(rbc_str[count])
        zbs[count] = float(zbs_str[count])
        count=count+1   

    # Set theta, phi values 
    dtheta = (2 * np.pi) / Ntheta
    dphi = (2 * np.pi) / Nphi
    filename3 = "3D_total.csv"
    output3 = open(filename3, "w")
    print("X,Y,Z",file=output3)

    phi_num = 0
    phi=0.0
    while phi_num <= Nphi:



        theta = 0.0
        theta_num = 0
        while theta_num <=Ntheta:

            R_sum =0.0 
            Z_sum = 0.0 
            count = 0

            while count <= tot_point-1:             
                R_sum = R_sum + (rbc[count])*(np.cos((m[count]*theta) - (n[count]*fp*phi)))
                Z_sum = Z_sum + (zbs[count])*(np.sin((m[count]*theta) - (n[count]*fp*phi)))
                count = count+1
          #Create coordinate file of different theta vals for same phi
            x = R_sum * np.cos(phi)
            y = R_sum * np.sin(phi)

            plasma_3D[phi_num,theta_num,0] = x 
            plasma_3D[phi_num,theta_num,1] = y 
            plasma_3D[phi_num,theta_num,2] = Z_sum 

            theta = theta + dtheta
            theta_num = theta_num + 1

            print(x,",",y,",",Z_sum,file=output3)

        phi = phi + dphi
        phi_num = phi_num + 1

    print("Coordinates converted from VMEC to RZ and 3D") 
    return (plasma_3D)
     
 
def RZ_to_VMEC(): 
    print("Converting to VMEC coordinates")

    #READ RZ coordinates  

#Run VMEC to RZ / 3D code
array2 = np.zeros((91,91,3))
#VMEC_TO_RZ("RZ_coords.csv",90,90,3,array2)
#print(array2[0,:,:])

#Run RZ to VMEC code 
#RZ_TO_VMEC("RZ_coords.csv",90,90)
