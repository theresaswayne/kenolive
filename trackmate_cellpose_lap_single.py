#@ File	(label="Input file", style="file") myInputFile
#@ File	(label="Output directory", style="directory") myOutputDir
#@ String  (label="Output name", value="_tracked") outputName
#@ String  (label="Channel for segmentation", choices={"0","1","2"}, style="listBox") detectorChannel

# based on https://forum.image.sc/t/jython-trackmate-cellpose-sam-cpsam-not-found-for-segment/120031/9

import sys
import os
import time

from java.io import File

from ij import IJ
from ij import ImagePlus
from ij import WindowManager

from fiji.plugin.trackmate import Model
from fiji.plugin.trackmate import Settings
from fiji.plugin.trackmate import TrackMate
from fiji.plugin.trackmate import SelectionModel
from fiji.plugin.trackmate import Logger
from fiji.plugin.trackmate.detection import LogDetectorFactory
from fiji.plugin.trackmate.tracking.jaqaman import SparseLAPTrackerFactory
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettingsIO
from fiji.plugin.trackmate.gui.displaysettings.DisplaySettings import TrackMateObject
from fiji.plugin.trackmate.features.track import TrackIndexAnalyzer

import fiji.plugin.trackmate.visualization.hyperstack.HyperStackDisplayer as HyperStackDisplayer
import fiji.plugin.trackmate.features.FeatureFilter as FeatureFilter

from fiji.plugin.trackmate.io import CSVExporter
from fiji.plugin.trackmate.visualization.table import TrackTableView

from fiji.plugin.trackmate.io import TmXmlWriter
from fiji.plugin.trackmate.util import LogRecorder
from fiji.plugin.trackmate.tracking.jaqaman import SparseLAPTrackerFactory
from fiji.plugin.trackmate.tracking.jaqaman import LAPUtils
from fiji.plugin.trackmate.util import TMUtils
from fiji.plugin.trackmate.cellpose.sam import CellposeSAMDetectorFactory
import fiji.plugin.trackmate.features.FeatureFilter as FeatureFilter
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettings
from fiji.plugin.trackmate.action import LabelImgExporter
from fiji.plugin.trackmate.action.LabelImgExporter import LabelIdPainting
from fiji.plugin.trackmate.action import CaptureOverlayAction
#from fiji.plugin.trackmate.cellpose import CellposeSettings
#from fiji.plugin.trackmate.cellpose.CellposeSettings import PretrainedModel
from fiji.plugin.trackmate.features.spot import SpotContrastAndSNRAnalyzerFactory, SpotIntensityMultiCAnalyzerFactory, SpotFitEllipseAnalyzerFactory, SpotShapeAnalyzerFactory
from fiji.plugin.trackmate.features.edges import EdgeSpeedAnalyzer, EdgeTargetAnalyzer, EdgeTimeLocationAnalyzer, DirectionalChangeAnalyzer
from fiji.plugin.trackmate.features.track import TrackBranchingAnalyzer, TrackDurationAnalyzer, TrackIndexAnalyzer, TrackLocationAnalyzer, TrackSpeedStatisticsAnalyzer, TrackMotilityAnalyzer

# ---- Setup ----

# We have to do the following to avoid errors with UTF8 chars generated in 
# TrackMate that will mess with our Fiji Jython.
reload(sys)
sys.setdefaultencoding('utf-8')

CELLPOSE_MODELS = os.path.join(os.path.expanduser(""), ".cellpose", "models")


# Get currently selected image
# imp = WindowManager.getCurrentImage()
#imp = IJ.openImage('https://fiji.sc/samples/FakeTracks.tif')
#imp.show()

# ---- Functions ----- 

## open image
def open_image(path):
	imp = IJ.openImage(path)
	if imp is None:
		sys.exit("Cannot open: " + path)
	imp.show()
	print("Opened: %s | (x,y,c,z,t) = %d %d %d %d %d" % (
		imp.getTitle(),
		imp.getWidth(), imp.getHeight(),
		imp.getNChannels(), imp.getNSlices(), imp.getNFrames()))
	IJ.run("Collect Garbage")
	return imp

## free memory

def close_original(imp):
	imp.changes = False
	imp.close()
	IJ.run("Collect Garbage")
	print("Original closed.")

## swap z and t because the stack will default to Z mode

def swap_zt(imp): # requires 2d stack
    IJ.selectWindow(imp.getTitle())
    imp.setDimensions(imp.getNChannels(), 1, imp.getNSlices())
    print("Swapped: (x,y,c,z,t) = %d %d %d %d %d" % (
        imp.getWidth(), imp.getHeight(),
        imp.getNChannels(), imp.getNSlices(), imp.getNFrames()))
    IJ.run("Collect Garbage")
    return imp
	
## TrackMate with LAP tracker

def run_trackmate(imp, channel):
	print('Starting TrackMate...')
	model = Model()
	model.setLogger(Logger.IJ_LOGGER)
	settings = Settings(imp)
	settings.initialSpotFilterValue = -1.
	settings.detectorFactory = CellposeSAMDetectorFactory()
	settings.detectorSettings = {
		'CELLPOSE_PYTHON_FILEPATH' : "/opt/anaconda3/envs/cellpose/bin/python",
		'CONDA_ENV' : 'cellpose',
		'TARGET_CHANNEL' : "0", # uses combo of all channels
		'CELLPOSE_MODEL' : "cpsam",
		'USE_GPU' : True,
		'SIMPLIFY_CONTOURS' : True
	}
	
	# Configure spot filters - Classical filter on quality
	filter1 = FeatureFilter('QUALITY', 30, True)
	settings.addSpotFilter(filter1)
	
	# Configure tracker - We want to allow merges and fusions
	settings.trackerFactory = SparseLAPTrackerFactory()
	settings.trackerSettings = settings.trackerFactory.getDefaultSettings() # almost good enough
	settings.trackerSettings['ALLOW_TRACK_SPLITTING'] = True # cells may divide
	settings.trackerSettings['ALLOW_TRACK_MERGING'] = False # cells won't fuse
	
	# Add ALL the feature analyzers known to TrackMate. They will 
	# yield numerical features for the results, such as speed, mean intensity etc.
	settings.addAllAnalyzers()
	
	# The line above is VERY IMPORTANT if you want to filter spots or tracks.
	# By default the TrackMate settings do not include feature analyzers, and the 
	# objects you will get from tracking will only include the very minimal 
	# feature set needed for TrackMate to operate. This might be advantageous
	# if you want to go fast. If you want however to compute specific features and / or
	# filter spots based on these filters, you need to explicitely include the corresponding
	# analyzer into the settings object. Filtering will not work without that. For instance,
	# if you try for  to filter spots with a feature that was not calculated by an analyzer,
	# you will have 0 spots after filtering.
	# With `settings.addAllAnalyzers()` we simply add all the analyzers that TrackMate 
	# can find. Since they are relatively fast, this is a convenient method.
	
	# Configure track filters - We want to get rid of the two immobile spots at
	# the bottom right of the image. Track displacement must be above 10 pixels.
	filter2 = FeatureFilter('TRACK_DISPLACEMENT', 10, True)
	settings.addTrackFilter(filter2)
	
	tm = TrackMate(model, settings)
	if not tm.checkInput(): sys.exit("checkInput: " + str(tm.getErrorMessage()))
	if not tm.process():	sys.exit("process: "	+ str(tm.getErrorMessage()))
	tm.computeSpotFeatures(True)
	tm.computeTrackFeatures(True)
	print("Tracks found: " + str(model.getTrackModel().nTracks(True)))
	IJ.run("Collect Garbage")
	return tm, model

## export xml TM

def save_trackmate_xml(model, settings_obj, path):
    writer = TmXmlWriter(File(path), Logger.IJ_LOGGER)
    writer.appendModel(model)
    writer.appendSettings(settings_obj)
    writer.writeToFile()
    print("TrackMate XML saved: " + path)


## export label image

def export_label_image(trackmate, imp_ref, path):
    SelectionModel(trackmate.getModel())
    label_imp = LabelImgExporter.createLabelImagePlus(
        trackmate, False, False, LabelIdPainting.LABEL_IS_TRACK_ID)
    label_imp.setCalibration(imp_ref.getCalibration())
    IJ.saveAsTiff(label_imp, path)
    label_imp.close()
    IJ.run("Collect Garbage")
    print("Label image saved: " + path)
    
# ---- Run ----

start_time = time.time()
base, ext = os.path.splitext(os.path.basename(str(myInputFile)))
imp = open_image(str(myInputFile))
imp = swap_zt(imp)
tm, model  = run_trackmate(imp, detectorChannel)
save_trackmate_xml(model, tm.getSettings(), os.path.join(str(myOutputDir), base + "_trackmate.xml"))
export_label_image(tm, imp, os.path.join(str(myOutputDir), base + "_labels.tif"))



#----------------
# Display results
#----------------

# A selection.
selectionModel = SelectionModel( model )

# Read the default display settings.
ds = DisplaySettingsIO.readUserDefault()
# Color by tracks.
ds.setTrackColorBy( TrackMateObject.TRACKS, TrackIndexAnalyzer.TRACK_INDEX )
ds.setSpotColorBy( TrackMateObject.TRACKS, TrackIndexAnalyzer.TRACK_INDEX )

displayer =  HyperStackDisplayer( model, selectionModel, imp, ds )
displayer.render()
displayer.refresh()

# Export all spots
out_file_csv = base + "_all_spots.csv"
only_visible = False # Export only visible 
# If you set this flag to False, it will include all the spots,
# the ones not in tracks, and the ones not visible.
CSVExporter.exportSpots(os.path.join(str(myOutputDir),out_file_csv), model, only_visible )

# Spot table. Will contain only the spots that are in visible tracks.
spots_in_tracks_table = TrackTableView.createSpotTable( model, ds )
#spot_table_csv_file = File( input_filename.replace( '.xml', '-spots.csv' ) )
spots_in_tracks_name = base + "_tracked_spots.csv"
spots_in_tracks_file = File(os.path.join(str(myOutputDir),spots_in_tracks_name))
spots_in_tracks_table.exportToCsv( spots_in_tracks_file )

# Track table.
track_table = TrackTableView.createTrackTable( model, ds )
tracks_name = base + "_tracks.csv"
track_table_csv_file = File(os.path.join(str(myOutputDir),tracks_name))
track_table.exportToCsv( track_table_csv_file )

# Echo results with the logger we set at start:
model.getLogger().log( str( model ) )

close_original(imp)

end_time = time.time()
elapsed_time = end_time - start_time

print("Finished in %s seconds." % elapsed_time)

