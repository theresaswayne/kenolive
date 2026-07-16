#@ File(label = "Input folder:", style = "directory") inDir
#@ File(label = "Output folder:", style = "directory") outDir
#@ String(label="Image File Extension", required=false, value=".tif") image_extension
#@ String  (label = "File name contains", value = "") containString

# Batch bleach correction in Fiji
# Theresa Swayne, 2024
# Adapted from Kota Miura's script at https://gist.github.com/miura/9080feb52eb74079ae393dd9320cb6ed 

# TO USE: Run the macro and specify folders for input and output, and select the image extension.

# Limitations: If the plugin finds that any dataset is "not decaying" it will stop.

# ---- Setup ----

import os
import math
import io
from net.imglib2.view import Views
from ij import IJ, ImagePlus, ImageStack
from ij.process import ImageProcessor, FloatProcessor, StackProcessor
import string
from emblcmci import BleachCorrection


# ---- Find image files ---- 
inputdir = str(inDir) # convert the directory object into a string
outputdir = str(outDir)
fnames = [] # empty array for filenames
for fname in os.listdir(inputdir):
	if fname.startswith("."): # avoid dotfiles that have the extension and filename filter
		continue
	if fname.endswith(image_extension):
		if containString not in fname:
			continue
		fnames.append(os.path.join(inputdir, fname)) # add matching file paths to the array
		
fnames = sorted(fnames) # sort the file names

if len(fnames) < 1: # no files
	raise Exception("No image files found in %s" % inputdir)

# ---- Loop through files ----
for fname in fnames: 
	print "Processing:",fname

	# Access the image
	IJ.log("Opening image file "+ fname)
	# imp = IJ.openImage(fname) # open the image normally
	imp = ImagePlus(fname) # for headless (faster and less glitchy)
	IJ.log("Stack size: " + str(imp.getStackSize()))
	
	bc = BleachCorrection() # prepare bleach correction
	
	# select method (comment out unused methods)
	
	### simple ratio method
	#bc.setHeadlessProcessing(True)
	#bc.setCorrectionMethod(BleachCorrection.SIMPLE_RATIO)
	#bc.setSimpleRatioBaseline(5) # can update with your own background level
	
	### exponential fit method
	bc.setCorrectionMethod(BleachCorrection.EXPONENTIAL_FIT)
	bc.setHeadlessProcessing(True)
	
	### Histogram Matching Method
	#bc.setCorrectionMethod(BleachCorrection.HISTOGRAM_MATCHING)
	#bc.setHeadlessProcessing(True)
	
	# perform correction
	impcorrected = bc.doCorrection(imp)
	
	#imp.show()
	#impcorrected.show()
	IJ.log("Finished correcting "+fname)

	outputName = string.join((os.path.basename(fname)[0:-4],"_corr", image_extension), "")
	# save the output image
	IJ.log("Saving to " + outputdir)
	IJ.saveAs(impcorrected, "Tiff", os.path.join(outputdir, outputName));
	#imp.close()
 
IJ.log("Finished")


