import pandas as pd
from sys import argv
import os
from os import path
import shutil
import starfile
import glob


def read_mdoc(mdocname):
    mdoc_header = ["Zvalue","MinMaxMean","TiltAngle","StagePosition","StageZ","Magnification","Intensity","ExposureDose","DoseRate","PixelSpacing","SpotSize","Defocus","ImageShift","RotationAngle","ExposureTime","Binning","CameraIndex","DividedBy2","OperatingMode","MagIndex","LowDoseConSet","CountsPerElectron","TargetDefocus","PriorRecordDose","SubFramePath","NumSubFrames","FrameDosesAndNumber","DateTime","NavigatorLabel","FilterSlitAndLoss"]
    mdoc_df = pd.DataFrame(data=None, index=None, columns=mdoc_header, dtype=None, copy=None)
    ind = 0
    with open(mdocname) as fh:
        for line in range(10):#skip the first 10 lines
            next(fh)
        for line in fh:
            entry = line.split(" = ")
            if entry[0] == "[ZValue":
                ind = ind + 1
                mdoc_df.at[ind, 'Zvalue'] = entry[1][0:-2]
                continue
            elif entry[0] == "\n":
                    continue
            else:
                mdoc_df.at[ind, entry[0]] = entry[1][0:-1]
                
    return mdoc_df

def read_ta(taSname,tilt_offset=0):
    if not path.exists(taSname):
            print("File not found:",taSname)
    if not path.exists(taSname+".bak"):
        print("Saving backup file:",taSname+".bak")
        shutil.copyfile(taSname,taSname+".bak")
    else:
        print("taSolution Backup file already exists:",taSname+".bak")
    
    df = pd.read_csv(taSname+".bak", index_col=0, skiprows=3, sep=None, skipinitialspace=True,header=None, names=ta_header)
    df["deltilt"] = df["deltilt"]+tilt_offset

    return df

def read_tomostar(tomostarname):
    if not path.exists(tomostarname):
            print("File not found:",tomostarname)
    if not path.exists(tomostarname+".bak"):
        print("Saving backup file:",tomostarname+".bak")
        shutil.copyfile(tomostarname,tomostarname+".bak")
    else:
        print("Tomostar Backup file already exists:",tomostarname+".bak")
    
    df = starfile.read(tomostarname+".bak")
    
    return df

def read_xml(xmlname):
    if not path.exists(xmlname):
            print("File not found:",xmlname)
    if not path.exists(xmlname+".bak"):
        print("Saving backup file:",xmlname+".bak")
        shutil.copyfile(xmlname,xmlname+".bak")
    else:
        print("Tomostar Backup file already exists:",xmlname+".bak")
    
       
    return df


datapath = "2022_0226_RTSS/"
framepath = datapath + "frames/"     
imodpath = framepath + "imod/"
mdocpath = datapath + "averages/"
tomolist = glob.glob(framepath + "*.tomostar")
tilt_offset = 0
tilt_invert = -1 #invert tilt angles in warp?
ta_header = ["view","rotation","tilt","deltilt","mag","dmag","skew","mean resid"]

for tomostarname in tomolist:
    tomoname = path.basename(tomostarname)
    tomoname = tomoname [0:-9]
    taSname = imodpath + tomoname + "/taSolution.log"
    mdocname = mdocpath + tomoname + ".mdoc"
    xmlname = framepath + tomoname + ".xml"
    if path.exists(taSname) and path.exists(tomostarname): 
        ta_df = read_ta(taSname,tilt_offset)
        mdoc_df = read_mdoc(mdocname)
        tomostar_df = read_tomostar(tomostarname)
        newtomostar_df = pd.DataFrame(None, columns = tomostar_df.columns)

        new_ind = 0
        for view in ta_df.index:
            if view > 10 and view < 50: #removing views for all tilt series
                new_ind = new_ind + 1
                mdocrow = mdoc_df.loc[mdoc_df['Zvalue'] == str(view - 1)]
                imagename =  mdocrow['SubFramePath'].values[0][mdocrow['SubFramePath'].values[0].rfind('frames\\'):][7:]
                #print(imagename)
                tomostarrow = tomostar_df.loc[tomostar_df['wrpMovieName']==imagename]
                if tomostarrow.index.values.size == 1:
                    tomostarrow.loc[tomostarrow.index.values[0],'wrpAngleTilt'] = tilt_invert * (float(mdocrow['TiltAngle'].values[0]) + ta_df.loc[view]['deltilt'])
                    tomostarrow.loc[tomostarrow.index.values[0],'wrpDose'] =  float(mdocrow['PriorRecordDose'].values[0]) + float(mdocrow['ExposureDose'].values[0])
                    newtomostar_df.loc[new_ind]=tomostarrow.loc[tomostarrow.index[0]]
        starfile.write(newtomostar_df, tomostarname,overwrite=True)
    if path.exists(xmlname):
        os.rename(xmlname, xmlname+'.bak')
        print("XML file found, please re-run the Warp process")
