#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Adapted by Benjamin Barad (benjamin.barad@gmail.com) from code by Digvijay Singh (digvijay.in1@gmail.com)
# Run in an mdocs folder, makes an "Adjusted_mdoc" subfolder with corrected angles, which allows more flexibility for 
# which program is used for tilt series alignment while guaranteeing a flat tomogram. I use it with etomo and warp primarily.

# Instead of identifying the "0" tilt based on transmission, you do it based on a predetermined milling angle.
# This has benefits and disadvantages, and is particularly useful if knowing absolute orientation is useful for future
# analysis.

# Usage:
# cd MDOC_FOLDER
# python pretilt_mdocs.py PRETILT

from sys import argv
import re
import glob, os

pretilt_angle = argv[1]

def adjust_mdoc(mdoc_file):
 exposure_times = []
 counts_per_electron = []
 mean_intensities = []
 tilt_angles = []

 with open(mdoc_file, "r") as input_file:
     if not os.path.exists('./Adjusted_mdoc'):
      os.makedirs('./Adjusted_mdoc')
     output_file = open('./Adjusted_mdoc/' + os.path.basename(mdoc_file), "w")
     for line in input_file:
      match2 = re.search('TiltAngle = ?(-?\d*.\d*)', line)
      match3 = re.search('bidir = ?(-?\d*.\d*)', line)
      if match2:
       new_tilt_angle = float(match2.group(1)) - pretilt_angle
       line = re.sub('TiltAngle = ?(-?\d*.\d*)',
                     'TiltAngle = ' + str(new_tilt_angle), line)
      if match3:
       new_bidirec_angle = float(match3.group(1)) - pretilt_angle
       line = re.sub('bidir = ?(-?\d*.\d*)', 'bidir = ' + str(new_bidirec_angle),
                     line)
      output_file.write(line)
     output_file.close()

for mdoc_file in glob.glob("*.mdoc"):
 adjust_mdoc(mdoc_file)
