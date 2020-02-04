# Sentinel Utilities

import subprocess
import os
import sys
import glob
import datetime as dt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt 
import matplotlib.dates as mdates
import numpy as np
import collections
import netcdf_read_write



def write_super_master_batch_config(masterid):
    ifile=open('batch.config','r');
    ofile=open('batch.config.new','w');
    for line in ifile:
        if 'master_image' in line:
            ofile.write('master_image = '+masterid+'\n');
        else:        
            ofile.write(line);
    ifile.close();
    ofile.close();
    subprocess.call(['mv','batch.config.new','batch.config'],shell=False);
    print("Writing master_image into batch.config");
    return;


def get_list_of_intfs(config_params):
    # This is where some hand-picking takes place
    select_intf_list=[];
    total_intf_list=glob.glob("F"+config_params.swath+"/intf_all/???????_???????/unwrap.grd");
    # total_intf_list=glob.glob("F"+config_params.swath+"/intf_all/2015349_2017338/unwrap.grd");
    # total_intf_list=glob.glob("F"+config_params.swath+"/intf_all/2019100_2019112/unwrap.grd");


    # IN A GENERAL CASE, WE WILL NOT BE SELECTING ONLY LONG INTERFEROGRAMS
    # THIS DEPENDS ON YOUR CONFIG SETTINGS
    # I THINK WE MIGHT WANT TO SELECT ALL INTERFEROGRAMS
    # FEB 2020
    select_criterion=0.8; # 3+ years, 2+ years, 1+ year

    for item in total_intf_list:
        dates = item.split("/")[-2];
        year1 = dates[0:4];
        year2 = dates[8:12];
        day1  = str(int(dates[4:7])+1);
        day2  = str(int(dates[12:15])+1);
        date1 = dt.datetime.strptime(year1+day1,"%Y%j")
        date2 = dt.datetime.strptime(year2+day2,"%Y%j")
        deltat = date2-date1
        if deltat.days > select_criterion*0.9*365: # a year plus or minus a month
            select_intf_list.append(item);

    print("Out of %d possible interferograms, we are trying to use %d" % (len(total_intf_list), len(select_intf_list)) );
    return select_intf_list;




def make_referenced_unwrapped(intf_list, swath, ref_swath, rowref, colref, ref_dir):
    # This works for both F1 and F2. You should run whichever swath has the reference point first. 
    # This will break for F3, because we need the F3-F2 offset and the F2-F1 offset. 
    output_dir="F"+swath+"/"+ref_dir;
    print("Imposing reference pixel on %d files; saving output in %s" % (len(intf_list), output_dir) );

    for item in intf_list:
        # Step 1: get reference offset
        individual_name=item.split('/')[-1];  # ex: unwrap.grd
        intf_name=item.split('/')[-2];  # ex: 2015178_2018180
        F1_name=item.replace('F'+swath,'F1');
        F2_name=item.replace('F'+swath,'F2');
        F3_name=item.replace('F'+swath,'F3');
        is1 = (os.path.isfile(F1_name));
        is2 = (os.path.isfile(F2_name));
        is3 = (os.path.isfile(F3_name)); 

        if swath=='1':
            # This is easy. We have no issues with 2*n*pi
            zvalue = get_reference_value(swath, ref_swath, rowref, colref, item);
        else:
            if is1==1 and is2==1 and swath=='2':  # 2 case
                zvalue_pixel = get_reference_value(ref_swath, ref_swath, rowref, colref, F1_name);  # the reference pixel in F1
                zvalue_2npi = get_n_2pi(F1_name, F2_name);  # this is an integer
                zvalue = zvalue_pixel+zvalue_2npi*-2*np.pi;

            elif is1==1 and is2==1 and is3==1 and swath=='3': # 3 case. 
                print("in swath 3. Will find n pi");
                F2_referenced = "F2/stacking/ref_unwrapped/"+intf_name+"_unwrap.grd"
                zvalue_pixel = get_reference_value(ref_swath, ref_swath, rowref, colref, F1_name);  # the reference pixel in F1
                zvalue_2npi_12 = get_n_2pi(F1_name, F2_name);  # this is an integer
                zvalue_2npi_23 = get_n_2pi(F2_name, F3_name);
                print("n is %d and %d" % (zvalue_2npi_12, zvalue_2npi_23) );
                zvalue = zvalue_pixel+zvalue_2npi_12*-2*np.pi+zvalue_2npi_23*-2*np.pi;
            else: # we don't have enough data to do the referencing.
                print("skipping making ref_unwrapped for %s " % item)
                continue;

        outname=output_dir+"/"+intf_name+"_"+individual_name;
        print("Making %s " % outname);
        [xdata,ydata,zdata] = netcdf_read_write.read_grd_xyz(item);
        referenced_zdata = apply_reference_value(xdata, ydata, zdata, zvalue);
        netcdf_read_write.produce_output_netcdf(xdata, ydata, referenced_zdata, 'phase', outname); 
    print("Done making reference unwrapped")
    return;

def get_n_2pi(file1, file2):
    # file1 must be the smaller number (F1)
    print(file1)
    print(file2)
    [xdata_f1,ydata_f1,zdata_f1] = netcdf_read_write.read_grd_xyz(file1);
    [xdata_f2,ydata_f2,zdata_f2] = netcdf_read_write.read_grd_xyz(file2);  
    n = (np.nanmean(zdata_f1[:,-20])-np.nanmean(zdata_f2[:,20]))/(2*np.pi);
    return np.round(n);


def apply_reference_value(xdata, ydata, zdata, reference_value):
    # The math component of applying a reference to a grid. 
    referenced_zdata=np.zeros(np.shape(zdata));
    for i in range(len(ydata)):
        for j in range(len(xdata)):
            referenced_zdata[i][j]=zdata[i][j]-reference_value;
    return referenced_zdata;


def get_reference_value(swath, ref_swath, rowref, colref, item):
    # Reading a file and putting it in the cache, or ignoring this scene due to lack of reference value. 
    if swath==ref_swath:
        [xdata,ydata,zdata] = netcdf_read_write.read_grd_xyz(item);
        reference_value = zdata[rowref][colref];
        # ofile=open(saving_file,'a');
        # ofile.write("%s %d %d %f %f\n" % (item, rowref, colref, reference_value, 0.0 ));
        # ofile.close();
    else:
        reference_value=np.nan;
        print("Skipping %s because we can't find it in F1" % item)
    return reference_value;


def get_ref_index(ref_swath, swath, ref_loc, ref_idx):
    # if swath != ref_swath:
    #     rowref, colref = 0, 0;  # this is a degenerate case, handled in make_referenced_unwrapped function. 
    # else:
    if ref_idx != []:  # if we already have an index location... 
        rowref=int(ref_idx.split('/')[0])
        colref=int(ref_idx.split('/')[1])
    else:
        rowref=0; colref=0;
        # Here we will run ll2ra in the future. 
    return rowref, colref;



