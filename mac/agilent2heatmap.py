#!/usr/bin/env python
#coding: utf8

import site
import sys
import os
import subprocess



import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import seaborn as sns
from datetime import datetime
import time

from gooey import Gooey, GooeyParser
#from message import display_message


@Gooey(program_name="Agilent OpenLab Datapreprocessing tool", default_size=(600,600), advanced=True, navigation="TABBED")




########################################################################################################################
############################################################################################################################################

#LIS https://pakstech.com/blog/python-gooey/  ABSCHNITT Alternative functionality with subparsers

############################################################################################################################################
########################################################################################################################
def main():

    desc = "Convert csv files (calibration or screening) from Agilent OpenLab outputs into processed excelfiles and plot the results"
    parser = GooeyParser(description=desc)

    #parser.add_argument('--verbose', help='be verbose', dest='verbose',
    #                    action='store_true', default=False)   ## ???

                        
    sub_parser = parser.add_subparsers(help='commands', dest='command')


############### REQUIRED ELEMENTS 

    datapreprocessing = sub_parser.add_parser( #parser name starts with capital letter Data..
        'Data_preprocessing',prog="Data Preprocessing", help='Convert the Agilent OpenLab output into an Excel file')  #.add_argument_group("File Handling data preprocessing") # Title of subsection in tab

    datapreprocessing.add_argument( #
        "calibration_file",metavar="Calibration Files", help="Choose the csv file which contains the calibration data ", widget="FileChooser", gooey_options=dict(wildcard="*.csv")) #only csv files

    datapreprocessing.add_argument( 
        "output_folder",metavar="Output Folder/Directory", help="Folder in which the output data will be saved", widget="DirChooser")

    datapreprocessing.add_argument( #
        "screening_file",metavar="Screening File",help="Choose the csv file which contains the screening data ", widget="FileChooser")

    datapreprocessing.add_argument( 
        "output_name", metavar="Output file name", help="Name of the output Excel file", type=str)

    datapreprocessing.add_argument( 
        "--outlier_sub", metavar="Outliers Substrate",widget="Listbox", choices=['0.1875', '0.25', '0.375', '0.5', '0.75', '1.0', '1.5', '2.0',
       '3.0'], nargs="+", help="Choose the to the concentration corresponding outliers for the substrate calibration", required=False)

    datapreprocessing.add_argument( 
        "--outlier_pro", metavar="Outliers Product", widget="Listbox", choices=['0.1875', '0.25', '0.375', '0.5', '0.75', '1.0', '1.5', '2.0',
       '3.0'], nargs="+", help="Choose the to the concentration corresponding outliers for the product calibration", required=False)

    datapreprocessing.add_argument( 
        "--dilution", metavar="Dilution factor", help="What is the dilution factor for the digestion quenching? Default = 5.0", type=float, default=5.0, required=False)


     

#    datapreprocessing.add_argument(
#        'Choose Output', choices=['Everything', 'Only heatmap'], 
#        help='Do you want to export the whole data preprocessing files (excel, calibration plot & heatmap) or only heatmap')

    heatmap_ = sub_parser.add_parser(
        'Heatmap', help='Convert the Agilent OpenLab output into a heatmap')
    
    

    heatmap_verb = heatmap_.add_mutually_exclusive_group(required=True)
    heatmap_verb.add_argument('--add_excel', metavar='Excel', ## Add if statement to choose read in code for final table either xlsx or csv
                           action="store_true", help="I will add an Excel file and the sheet name")
    heatmap_verb.add_argument('--add_csv', metavar='CSV',
                           action="store_true", help="I will add an csv file")

    heatmap = heatmap_.add_argument_group("Data Input/Output")

    heatmap.add_argument( 
        "heatmap_file", metavar="Heatmap file",help="Choose the csv or Excel file to the final Table for the heatmap", widget="FileChooser")

    heatmap.add_argument( 
        "heatmap_folder",metavar="Output Folder/Directory", help="Folder in which the output heatmap will be saved", widget="DirChooser")


    heatmap.add_argument( 
        "--sheet_name", metavar="Sheet name",help="If you choose an Excel file please write the name of the sheet", type=str)

    heatmap.add_argument( 
        "heatmap_name", metavar="Heatmap name",help="Name the JPEG output file", type=str)

    heatmap.add_argument( 
        "ConcRange", metavar="Concentration range",help="Change the max. concentration shown in the heatmap", type=float, default=None, required=False)

    heatmap.add_argument("--orientation", metavar="Orientation of heatmap", choices=["horizontal", "vertical"], help="Do you want the plot to be horizontal or vertical?")


    sub_parser_arg = parser.parse_args()
    run(sub_parser_arg)     # Assign arguments to variables  


def run(args):      #
    #global cal_csv, out_dir, screen_csv, excel_name, heatmap_file, heatmap_sheet, excel_choice

    if args.command == "Data_preprocessing":  ## If function depending which TAB was filled out
        cal_csv = args.calibration_file
        out_dir = args.output_folder
        screen_csv = args.screening_file
        output_name = args.output_name
        dilution = args.dilution

        if args.outlier_sub:
            outlier_sub = args.outlier_sub#.astype(float)
        else: outlier_sub =""

        if args.outlier_pro:
            outlier_pro = args.outlier_pro#.astype(float)
        else: 
            outlier_pro =""

        DataPreprocessing(cal_csv, out_dir, screen_csv, output_name, dilution, outlier_sub, outlier_pro) # ACHTUNG MUSS GLEICHE REIHENFOLGE HABEN WIE BEI DEF dATAPREPROCESSING
        
           
    elif args.command == "Heatmap":  #
        heatmap_file    = args.heatmap_file
        heatmap_folder  = args.heatmap_folder
        heatmap_sheet   = args.sheet_name
        heatmap_name    = args.heatmap_name
        ConcRange       = args.ConcRange
        heatmap_orientation = args.orientation

        if args.add_excel:
            excel_choice = True
        else:
            excel_choice = False
        HeatmapPlotter(heatmap_file,excel_choice, heatmap_folder, heatmap_sheet, heatmap_name, ConcRange, heatmap_orientation)
        #print(heatmap_file, heatmap_sheet, excel_choice)

############################################################################################################################################
def DataPreprocessing(cal_csv_InFun,out_dir_InFun,screen_csv_InFun, output_name="", dilution=5.0, outlier_sub_InFun="", outlier_pro_InFun=""): #
    
############################################################################################################################################


#ok = input("Dont forget! No Sample names starting with f(lush) or w(wash)")

    subwhat = output_name

    pfad_kal = cal_csv_InFun

    pfad_screen = screen_csv_InFun

    pfad_res = out_dir_InFun

    verdünnung = dilution

    #Names for variables, not important for user
    #sub = str(input("Which Substanze are you analysing ex: 5)"))
    sub = ""

    suba = sub+"a"
    subb = sub+"br"

    konzentration = "konz"
    subkonza = konzentration+" "+sub+"a"
    subkonzb = konzentration+" "+sub+"br"

    #titles for the plots
    #subname = str(input("What is the name of the substance ex: OPBE)"))
    subname =""
    #proname = str(input("What is the name of the product ex: R-OPBE)"))
    proname=""

    kal = pd.read_csv(pfad_kal, sep=";" )
    kal_original = pd.read_csv(pfad_kal, sep=";" )
    scr = pd.read_csv(pfad_screen, sep=";")


    ######################################    Kalibration    #########################################

    konz = {'konz': [0.1875, 0.25, 0.375, 0.5, 0.75, 1, 1.5, 2, 3]}

    konz_dict = ['0.1875', '0.25', '0.375', '0.5', '0.75', '1.0', '1.5', '2.0','3.0']
    konz_position_dict = np.array([0,1,2,3,4,5,6,7,8,9])#.astype(str)
    konz_position_dict = dict(zip(konz_dict , konz_position_dict))

    kalibration = pd.DataFrame(konz)

    def filter_kal(data_kal_start):
        global a, br, bs, kali,  data
        data = data_kal_start.copy()

        #erste spalte
        data['Unnamed: 0'].astype(str, copy=True, errors='raise')
        data['Unnamed: 0'] = data['Unnamed: 0'].fillna('Name')
        data.iloc[:,1:].fillna(0)
        data.drop(data.columns[[1, 2]], axis=1, inplace=True)
        # schmeiss raus falls flush, also mit name mit f beginnt
        for row, name in enumerate(data['Unnamed: 0']):
            print(row)
            print("Kal_fil__no_flush")
            if name.startswith('f') == True or name.startswith('w') == True:
                print("kal_filter_flush")
                data = data.drop([row])


        #restliche spalten
        data = data.fillna(0)
        data.iloc[1:,1:] = data.iloc[1:,1:].astype(float, copy=True, errors='raise')
        data.reset_index(drop=True, inplace=True)


        #a = np.array(data.iloc[1:,2][data.iloc[1:,2] > data.iloc[1,2] -10] )
        a = np.array(data.iloc[1:10, 2])
        #br = np.array(data.iloc[1:,4][data.iloc[1:,4] > data.iloc[10,4] -10])
        br = np.array(data.iloc[10:19, 4])
        #bs = np.array(data.iloc[1:,6][data.iloc[1:,6] > data.iloc[10,6] -10])
        bs = np.array(data.iloc[10:18, 6])
        kali = pd.DataFrame({'konz': [0.1875, 0.25, 0.375, 0.5, 0.75, 1, 1.5, 2, 3], subkonza:a, subkonzb:br} ) #'konz 4a':a, """'konz 4br':br.astype(float)} """

        return data, kali

    #create the calibration data
    kal_fil, kalibration_tot = filter_kal(kal)

    kalibration_tot=kalibration_tot.astype(float)

    #sammle ausreisser edukt
    #fit_outliers_educt = input("Any outliers for the educt? if yes, which? ex: 1,2,6 = second, third and seventh. If no, hit Enter")
    
    #wandle input in ndarray
    #fit_outliers_educt = np.fromstring(fit_outliers_educt, dtype=int, sep=',')
    fit_outliers_educt = np.array([konz_position_dict.get(key) for key in outlier_sub_InFun])#.astype(int)  # nehme input von listbox und wandle mittels definiertem dict (konz_position_dict) in integer array um

    #mache fit
    if fit_outliers_educt == "":
        a_m, a_ys = np.polyfit(kalibration_tot['konz'], kalibration_tot[subkonza], 1)
    else:
        a_m, a_ys = np.polyfit(kalibration_tot['konz'].drop(fit_outliers_educt, errors='ignore'), kalibration_tot[subkonza].drop(fit_outliers_educt, errors='ignore'), 1)


    #sammle ausreisse produkt
    #fit_outliers_product = input("Any outliers for the product? if yes, which? ex: 1,2,6 = second, third and seventh. If no, hit Enter")
    #wandle input in ndarray
    #fit_outliers_product = np.fromstring(fit_outliers_product, dtype=int, sep=',') #

    fit_outliers_product = np.array([konz_position_dict.get(key) for key in outlier_pro_InFun])#.astype(int)

    #mache fit
    if fit_outliers_product == "":
        b_m, b_ys = np.polyfit(kalibration_tot['konz'], kalibration_tot[subkonzb], 1)
    else:
        b_m, b_ys = np.polyfit(kalibration_tot['konz'].drop(fit_outliers_product, errors='ignore'), kalibration_tot[subkonzb].drop(fit_outliers_product, errors='ignore'), 1)


    #Plote Kalibration mit berècksichtigung der Ausreisser

    #kal_plot_a = kalibration_tot.plot(kind="scatter", x="konz", y=subkonza, grid=True)
    #kal_plot_b = kalibration_tot.plot(kind="scatter", x="konz", y=subkonzb, grid=True)

    _ = sns.regplot(x=kalibration_tot['konz'].drop(fit_outliers_educt, errors='ignore'), y=kalibration_tot[subkonza].drop(fit_outliers_educt, errors='ignore'), label=(suba+" "+subname), color='red')
    _ = sns.regplot(x=kalibration_tot['konz'].drop(fit_outliers_product, errors='ignore'),y=kalibration_tot[subkonzb].drop(fit_outliers_product, errors='ignore'), label=(subb+" "+proname), color='blue')

    _.set_xlabel('Concentration [mM]')
    _.set_ylabel('Peak area [mAU]')
    _.grid()

    #_.text(1,1,r'$a_m$')
    #formel = str(round(a_m,2)) + " x " + str(round(a_ys,2))
    #_.plot([], [], label=formel)

    _.legend()

    datename = datetime.now().strftime("%Y%m%d-%H%M%S")

    #name for date,
    name_fig_kal = datename + output_name + " calibration_plot"

    #safe regression parameters and fig
    sub_pro_param = {"Slope":[a_m,b_m], "Y intercept":[a_ys,b_ys]}
    reg_param = pd.DataFrame(sub_pro_param, columns=["Slope", "Y intercept"], index=["Substrate", "Product"])
    reg_param.to_csv(out_dir_InFun + "\\" + name_fig_kal + "_RegressionParameters.txt", sep="\t")

    _.figure.savefig(out_dir_InFun + "\\" + name_fig_kal + ".jpeg", format='jpeg', dpi=1000)
    plt.show()

    ####################################      Screening     ###################################################################


    def filter_screen(data_scr_start):
        global a4, br4, bs4, kali, data, name
        """data.drop(data.columns[[1,2]], axis=1, inplace=True)
        data = data[np.logical_or(data.iloc[:,1].notnull()==True, data.iloc[:,3].notnull()==True)]
        data = data.iloc[1:,:]
        data.iloc[:,1:] = data.iloc[:,1:].astype(float, copy=True, errors='raise')
        data.reset_index(drop=True, inplace=True)
        for a in range(1,len(data.columns)):
            for i in range(1, len(data.iloc[:,0])):
                if np.isnan(data.iloc[i, a]) == True:
                    data.iloc[i, a] = 0"""


        data = data_scr_start.copy()

        #erste spalte
        data['Unnamed: 0'].astype(str, copy=True, errors='raise')
        data['Unnamed: 0'] = data['Unnamed: 0'].fillna('Name')
        data.iloc[:,1:].fillna(0)
        data.drop(data.columns[[1, 2]], axis=1, inplace=True)
        # schmeiss raus falls flush, also mit name mit f beginnt
        for row, name in enumerate(data['Unnamed: 0']):
            print(row)
            if name.startswith('f') == True or name.startswith('N') == True:
                print(row)
                data = data.drop([row])


        #restliche spalten
        data = data.fillna(0)
        data.iloc[0:,1:] = data.iloc[0:,1:].astype(float)
        data.reset_index(drop=True, inplace=True)
        #nehme name
        probename = np.array(data['Unnamed: 0'])
        print(probename)

        a = np.array(data['Unnamed: 4'].values)
        konz_a = ((a - a_ys) / a_m )*verdünnung
        br = np.array(data['Unnamed: 6'])
        konz_br = ((br - b_ys) /  b_m )*verdünnung
        bs = np.array(data['Unnamed: 8'])
        konz_bs = ((bs - b_ys) / b_m )*verdünnung

        """
        a = np.array(data['Unnamed: 4'])
        konz_a = a
        br = np.array(data['Unnamed: 6'])
        konz_br = br
        bs = np.array(data['Unnamed: 8'])
        konz_bs = bs
        """
        screen = pd.DataFrame({'Probe': probename, 'Area a': a.astype(float), 'Konz a': konz_a.astype(float), 'Area b-r': br.astype(float), 'Konz b-r': konz_br.astype(float), 'Area b-s': bs.astype(float), 'Konz b-s': konz_bs.astype(float)})

        return data, screen

    screen_fil, screen = filter_screen(scr)

  
    #save end csv file
    #screen.to_csv(pfad_res + subwhat +"_"+ filename + ".csv", sep=",")
    screen.to_csv(out_dir_InFun + "/" + datename + output_name + ".csv", sep=",")
    print("You're Results have been saved in the location "+ out_dir_InFun)


############################################################################################################################################




def HeatmapPlotter(heatmap_file_InFun, excel_choice_InFun, heatmap_folder, 
                    heatmap_sheet_InFun="", heatmap_name="", ConcRange = None, heatmap_orientation="horizontal"): #
    

    pfad_excel = heatmap_file_InFun

    if excel_choice_InFun == True:
        data_matrix_raw = pd.read_excel(pfad_excel, sheet_name=heatmap_sheet_InFun, header=0, index_col=0)
    else:
        data_matrix_raw = pd.read_csv(pfad_excel, sep=";", header=0, index_col=0)


    print("""Please close the excel sheet after transfering the dataframe""")
    time.sleep(5)

    #read in data from excel

    #sub_plot = input("which substrates do you want to plot? ex: 1,6 means sub 1 and 6.  Hit Enter for all")
    #split input by comma

    '''if sub_plot != "":
        #make a an index type
        col = pd.Index([])
        sub_plot.split(",")
        for i in sub_plot:
        col = col.append(data_matrix_raw.columns[data_matrix_raw.columns.str.contains(i)==True])
        data_matrix = data_matrix_raw[col]
    elif sub_plot == "":
        data_matrix = data_matrix_raw
        print("ok")'''
    
    data_matrix = data_matrix_raw

    #read the substrate names
    sub = data_matrix.columns.to_list()
    #read the scaffold names
    sca = data_matrix.index.to_list()
    #transpose the matrix to have horizontal plot
    data_matrix_T = data_matrix.T.values

    name_save = heatmap_name
    save = heatmap_folder
    #see = input("Do you want to check (c) the plot or save (s) it directly? ")

    #change orientation of 
    ausrichtung = heatmap_orientation

    #code for the plot, if you want to change the looks, ticks, konzentration values
    #If you want to change the white grid then change the linewidth in line 321 --> ax.grid(which="minor", color="w", linestyle='-', linewidth=3)

    def heatmap(data, row_labels, col_labels, ax=None,
                cbar_kw={}, cbarlabel="", **kwargs):
        """
        Create a heatmap from a numpy array and two lists of labels.

        Parameters
        ----------
        data
            A 2D numpy array of shape (N, M).
        row_labels
            A list or array of length N with the labels for the rows.
        col_labels
            A list or array of length M with the labels for the columns.
        ax
            A `matplotlib.axes.Axes` instance to which the heatmap is plotted.  If
            not provided, use current axes or create a new one.  Optional.
        cbar_kw
            A dictionary with arguments to `matplotlib.Figure.colorbar`.  Optional.
        cbarlabel
            The label for the colorbar.  Optional.
        **kwargs
            All other arguments are forwarded to `imshow`.
        """

        if not ax:
            ax = plt.gca()

        # Plot the heatmap
        im = ax.imshow(data, **kwargs)

        # Create colorbar, mit pad bestimmst du abstand zwischen colorbar und heatmap


        if ausrichtung == "horizontal":
            ### FÜR QUEEEER
            cbar = ax.figure.colorbar(im, ax=ax, **cbar_kw, orientation=ausrichtung, pad=0.07)
            #cbar.ax.set_ylabel(cbarlabel, va="center", rotation=90) #, nur für titel
            cbar.ax.set_title('Umsatz [mM]')
            #passe ticks den Werten an, mit base bestimmst du tick abstände
            loc = plticker.MultipleLocator(base=0.5)  # this locator puts ticks at regular intervals

            cbar.ax.xaxis.set_major_locator(loc)

            # We want to show all ticks...
            ax.set_xticks(np.arange(data.shape[1]))
            ax.set_yticks(np.arange(data.shape[0]))
            # ... and label them with the respective list entries.
            ax.set_xticklabels(col_labels, size=7)
            ax.set_yticklabels(row_labels, size=7)



        elif ausrichtung == "vertical":
            ## FÜR HOOOOOCH
            cbar = ax.figure.colorbar(im, ax=ax, **cbar_kw, orientation=ausrichtung, pad=0.03) #pad vorher 0.07
            cbar.ax.set_ylabel(cbarlabel, va="center", rotation=90) #, nur für titel
            #cbar.ax.set_title('Umsatz / mM')
            #passe ticks den Werten an, mit base bestimmst du tick abstände
            loc = plticker.MultipleLocator(base=0.5)  # this locator puts ticks at regular intervals
            cbar.ax.yaxis.set_major_locator(loc)

            # We want to show all ticks...
            ax.set_xticks(np.arange(data.shape[1]))
            ax.set_yticks(np.arange(data.shape[0]))
            # ... and label them with the respective list entries.
            ax.set_xticklabels(col_labels, size=5)
            ax.set_yticklabels(row_labels, size=5)

        else:
            print("whot")




        # Let the horizontal axes labeling appear on top.
        ax.tick_params(top=True, bottom=False,
                    labeltop=True, labelbottom=False)

        # Rotate the tick labels and set their alignment.
        plt.setp(ax.get_xticklabels(), rotation=-40, ha="right",
                rotation_mode="anchor")

        # Turn spines off and create white grid.
        #ax.spines[:].set_visible(False)

        ax.set_xticks(np.arange(data.shape[1]+1)-.5, minor=True)
        ax.set_yticks(np.arange(data.shape[0]+1)-.5, minor=True)
        ax.grid(which="minor", color="w", linestyle='-', linewidth=3)
        #ax.grid(which="minor", color="grey", linestyle='-', linewidth=0.5)
        ax.tick_params(which="minor", bottom=False, left=False)

        return im, cbar

    print(data_matrix)

    if ausrichtung == 'horizontal' or "":
        plt.figure(figsize=(30, 10))
        fig, ax = plt.subplots()
        
        if not ConcRange:
            vmax = int(round(np.max(data_matrix_T)+0.5))
        else:
            vmax = ConcRange

        im, cbar = heatmap(data_matrix_T, sub, sca, ax=ax, cmap="BuPu", cbarlabel="Transformation [mM]", vmin=0, vmax=vmax) #vmax=int(round(max(data_matrix_T)+0.5)) vmin and max stands for min and max values in konzentration bar
        #only show every second tick
        for label in cbar.ax.xaxis.get_ticklabels()[::2]:
            label.set_visible(False)
        fig.tight_layout()
        fig.savefig(save + "\\" + name_save + ".jpeg" , format='jpeg', dpi=2000)
        plt.show()
        print("your file has been saved. Have a nice day :)")
    elif ausrichtung == 'vertical':
        plt.figure(figsize=(10, 30))
        fig, ax = plt.subplots()

        if not ConcRange:
            vmax = int(round(np.max(data_matrix_T)+0.5))
        else:
            vmax = ConcRange

        im, cbar = heatmap(data_matrix, sca, sub, ax=ax, cmap="BuPu", cbarlabel="Transformation [mM]", vmin=0, vmax=vmax )
        fig.tight_layout()
        fig.savefig(save +"\\"+ name_save + ".jpeg", format='jpeg', dpi=2000)
        plt.show()
        print("your file has been saved. Have a nice day :)")
    else: pass



if __name__ == '__main__':
    main()




############### OPTIONAL ELEMENTS
'''
    file_help_msg = "Name of the file you want to process"

    parser.add_argument('-d', '--duration', default=2,
                                type=int, help='Duration (in seconds) of the program output')
    parser.add_argument('-s', '--cron-schedule', type=int,
                                help='datetime when the cron should begin', widget='DateChooser')
    parser.add_argument('--cron-time', 
                                help='datetime when the cron should begin', widget="TimeChooser")
    parser.add_argument(
        "-c", "--showtime", action="store_true", help="display the countdown timer")
    parser.add_argument(
        "-p", "--pause", action="store_true", help="Pause execution")
    parser.add_argument('-v', '--verbose', action='count')
    parser.add_argument(
        "-o", "--overwrite", action="store_true", help="Overwrite output file (if present)")
    parser.add_argument(
        '-r', '--recursive', choices=['yes', 'no'], help='Recurse into subfolders')
    parser.add_argument(
        "-w", "--writelog", default="writelogs", help="Dump output to local file")
    parser.add_argument(
        "-e", "--error", action="store_true", help="Stop process on error (default: No)")
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument('-t', '--verbozze', dest='verbose',
                           action="store_true", help="Show more details")
    verbosity.add_argument('-q', '--quiet', dest='quiet',
                           action="store_true", help="Only output on error")

def here_is_more():
    pass
'''

