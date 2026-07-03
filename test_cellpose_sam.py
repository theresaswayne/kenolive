import sys
from ij import IJ, WindowManager
from ij.plugin import Slicer
from fiji.plugin.trackmate import Model, Settings, TrackMate, Logger, SelectionModel
from fiji.plugin.trackmate.cellpose.sam import CellposeSAMDetectorFactory
from fiji.plugin.trackmate.tracking.overlap import OverlapTrackerFactory
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettingsIO
from fiji.plugin.trackmate.gui.displaysettings.DisplaySettings import TrackMateObject
from fiji.plugin.trackmate.features.track import TrackIndexAnalyzer
import fiji.plugin.trackmate.visualization.hyperstack.HyperStackDisplayer as HyperStackDisplayer

# from https://forum.image.sc/t/jython-trackmate-cellpose-sam-cpsam-not-found-for-segment/120031/9

imp = WindowManager.getCurrentImage()
channel = 1
min_iou = 0.3
scale_factor = 1.
iou_method = 'PRECISE'

#CELLPOSE_PYTHON = "/opt/anaconda3/envs/cellpose/bin/python"



model = Model()
model.setLogger(Logger.IJ_LOGGER)
settings = Settings(imp)
settings.initialSpotFilterValue = -1.
settings.detectorFactory = CellposeSAMDetectorFactory()
settings.detectorSettings = {
    'TARGET_CHANNEL'         : str(channel),
    'OPTIONAL_CHANNEL_2'     : '0',
    'SIMPLIFY_CONTOURS'      : True,
    'USE_GPU'                : True,
    'CONDA_ENV'              : 'cellpose',
    'CELLPOSE_MODEL'         : 'cpsam',
    'CELLPOSE_MODEL_FILEPATH': '',
    'PRETRAINED_OR_CUSTOM'   : 'CELLPOSE_MODEL',
    'CELL_DIAMETER'          : 0.0,
}
settings.trackerFactory = OverlapTrackerFactory()
settings.trackerSettings = OverlapTrackerFactory().getDefaultSettings()
settings.trackerSettings['MIN_IOU']         = float(min_iou)
settings.trackerSettings['SCALE_FACTOR']    = float(scale_factor)
settings.trackerSettings['IOU_CALCULATION'] = str(iou_method)
settings.addAllAnalyzers()
tm = TrackMate(model, settings)

if not tm.checkInput(): sys.exit("checkInput: " + str(tm.getErrorMessage()))
if not tm.process():    sys.exit("process: "    + str(tm.getErrorMessage()))
tm.computeSpotFeatures(True)
tm.computeTrackFeatures(True)

print("Tracks found: " + str(model.getTrackModel().nTracks(True)))


# A selection.
selectionModel = SelectionModel( model )
 
# Read the default display settings.
ds = DisplaySettingsIO.readUserDefault()
ds.setTrackColorBy( TrackMateObject.TRACKS, TrackIndexAnalyzer.TRACK_INDEX )
ds.setSpotColorBy( TrackMateObject.TRACKS, TrackIndexAnalyzer.TRACK_INDEX )
 
displayer =  HyperStackDisplayer( model, selectionModel, imp, ds )
displayer.render()
displayer.refresh()