import pandas as pd
import click
import os
from os import path
import shutil
import starfile
import glob


def read_mdoc(mdocname):
    mdoc_header = ["Zvalue","MinMaxMean","TiltAngle","StagePosition","StageZ","Magnification","Intensity","ExposureDose","DoseRate","PixelSpacing","SpotSize","Defocus","ImageShift","RotationAngle","ExposureTime","Binning","CameraIndex","DividedBy2","OperatingMode","MagIndex","LowDoseConSet","CountsPerElectron","TargetDefocus","PriorRecordDose","SubFramePath","NumSubFrames","FrameDosesAndNumber","DateTime","NavigatorLabel","FilterSlitAndLoss"]
    #mdoc_type = ["string","string","float","float","float","float","float","float","float","float","string","float","float","float","float","string","string","string","string","string","float","float","float","float","string","int","string","string","string","string"]
    
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
    
    mdoc_df[['TiltAngle']] = mdoc_df[['TiltAngle']].apply(pd.to_numeric) 
    mdoc_df = mdoc_df.sort_values(by=['TiltAngle'])
    mdoc_df = mdoc_df.reset_index()
    mdoc_df['Zvalue']=mdoc_df.index.values
    return mdoc_df

def read_ta(taSname,ta_header):
    if not path.exists(taSname):
            print("File not found:",taSname)
    if not path.exists(taSname+".bak"):
        print("Saving backup file:",taSname+".bak")
        shutil.copyfile(taSname,taSname+".bak")
    else:
        print("taSolution Backup file already exists:",taSname+".bak")
    with open(taSname) as fh:
        #get the line number that has the string view in it
        skiprownumber = 0
        for line in fh:
            skiprownumber = skiprownumber + 1
            if "view" in line:
                break  
        
    df = pd.read_csv(taSname, index_col=0, skiprows=skiprownumber, sep=None, skipinitialspace=True,header=None, names=ta_header, engine='python')
    #df["deltilt"] = df["deltilt"]

    return df

def read_tomostar(tomostarname):
    if not path.exists(tomostarname):
            print("File not found:",tomostarname)
    if not path.exists(tomostarname+".bak"):
        print("Saving backup file:",tomostarname+".bak")
        shutil.copyfile(tomostarname,tomostarname+".bak")
    
    df = starfile.read(tomostarname)
    
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

@click.command()
@click.option('--frame_dir', help='Frame folder name', required=True, default='frames')
@click.option('--mdoc_dir', help='Path for mdoc files', required=True)
@click.option('--etomo_tilt', help='Use etomo-solved tilt instead of taking the deltilt.', is_flag=True, default=False, required=True)
def process_tomostars(frame_dir, mdoc_dir,etomo_tilt):
    framepath =  frame_dir + "/"     
    imodpath = framepath + "imod/"
    tomolist = glob.glob(framepath + "*.tomostar")
    tilt_offset = 0.0

    ta_header = ["view","rotation","tilt","deltilt","mag","dmag","skew","mean resid"]
    
    for tomostarname in tomolist:
        print(tomostarname)
        # take the basename of tomostarname without extension
        tomoname = os.path.splitext(os.path.basename(tomostarname))[0]
        taSname = imodpath + tomoname + "/taSolution.log"
        mdocname = mdoc_dir + tomoname + ".mdoc"
        xmlname = framepath + tomoname + ".xml"
        if path.exists(taSname) and path.exists(tomostarname): 
            ta_df = read_ta(taSname,ta_header)
            mdoc_df = read_mdoc(mdocname)
            tomostar_df = read_tomostar(tomostarname)
            newtomostar_df = pd.DataFrame(None, columns = tomostar_df.columns)

            new_ind = 0
            print(taSname)
            print(ta_df.index)
            for view in ta_df.index:
                view = int(view)
                new_ind = new_ind + 1
                mdocrow = mdoc_df.loc[mdoc_df['Zvalue'] == view - 1]
                framefindstr = frame_dir + '\\'
                imagename = os.path.basename(mdocrow['SubFramePath'].values[0]) #[mdocrow['SubFramePath'].values[0].rfind(framefindstr):]
                #imagename = imagename.replace(framefindstr,"")
                
                tomostarrow = tomostar_df.loc[tomostar_df['wrpMovieName']==imagename]
                if tomostarrow.index.values.size == 1:
                    tomostarrow.loc[tomostarrow.index.values[0],'wrpDose'] =  (mdoc_df['index'][view-1] - 0.5) * float(mdoc_df['ExposureDose'][view-1])  
                    if etomo_tilt:
                        print(view, tomostarrow.loc[tomostarrow.index.values[0],'wrpAngleTilt'],ta_df.loc[view]['tilt'])
                        tomostarrow.loc[tomostarrow.index.values[0],'wrpAngleTilt'] = ta_df.loc[view]['tilt']
                    newtomostar_df.loc[new_ind]=tomostarrow.loc[tomostarrow.index[0]]
                    print(tomostarrow.loc[tomostarrow.index[0]])
            starfile.write(newtomostar_df, tomostarname,overwrite=True)
        if path.exists(xmlname):
            os.rename(xmlname, xmlname+'.bak')
            print("XML file found, please re-run the Warp process")  

if __name__ == '__main__':
    process_tomostars()
