#@ File    (label="Input file", style="open") myInputFile
#@ File    (label="Output directory", style="directory") myOutputDir
#@ String  (label="Output name", value="resliced") outputName
#@ Float   (label="Spacing Z (um)", value=2.636) spacingZ
#@ String  (label="Canal segmentation", choices={"0","1","2"}, style="listBox") detectorChannel
#@ Float   (label="Min IoU", value=0.3, min=0.0, max=1.0) minIoU
#@ Float   (label="Scale factor", value=1.0, min=0.5, max=2.0) scaleFactor
#@ String  (label="Methode IoU", choices={"PRECISE","FAST"}, style="listBox") iouMethod

# from https://forum.image.sc/t/jython-trackmate-cellpose-sam-cpsam-not-found-for-segment/120031/9

import sys, os
reload(sys)
sys.setdefaultencoding('utf-8')

from ij import IJ, WindowManager
from ij.plugin import Slicer
from fiji.plugin.trackmate import Model, Settings, TrackMate, Logger
from fiji.plugin.trackmate.action import LabelImgExporter
from fiji.plugin.trackmate.action.LabelImgExporter import LabelIdPainting
from fiji.plugin.trackmate import SelectionModel
from fiji.plugin.trackmate.cellpose.sam import CellposeSAMDetectorFactory
from fiji.plugin.trackmate.tracking.overlap import OverlapTrackerFactory
from fiji.plugin.trackmate.io import TmXmlWriter
from java.io import File


CELLPOSE_PYTHON = "/opt/anaconda3/envs/cellpose/bin/python"
CELLPOSE_MODELS = os.path.join(os.path.expanduser(""), ".cellpose", "models")

# fonctions

## 1. open .czi

def open_czi(path):
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


## 2. reslice n swap

def reslice_and_swap(imp, spacing_z):
    IJ.selectWindow(imp.getTitle())
    Slicer().run("output=" + str(spacing_z) + " start=Top")
    imp_r = IJ.getImage()
    imp_r.setTitle("resliced_" + imp.getTitle())
    imp_r.setDimensions(imp_r.getNChannels(), 1, imp_r.getNSlices())
    print("Resliced + swapped: (x,y,c,z,t) = %d %d %d %d %d" % (
        imp_r.getWidth(), imp_r.getHeight(),
        imp_r.getNChannels(), imp_r.getNSlices(), imp_r.getNFrames()))
    IJ.run("Collect Garbage")
    return imp_r

## 3. free memory

def close_original(imp):
    imp.changes = False
    imp.close()
    IJ.run("Collect Garbage")
    print("Original closed.")


## 4. export xml

def export_bdv(imp, output_path):
    IJ.run(imp, "Export Current Image as XML/HDF5",
        "subsampling_factors=[{ {1,1,1}, {2,2,1}, {4,4,1}, {8,8,2}, {16,16,4}, {32,32,8} }] "
        "hdf5_chunk_sizes=[{ {32,32,4}, {32,16,8}, {16,16,16}, {16,16,16}, {16,16,16}, {16,16,16} }] "
        "timepoints_per_partition=0 setups_per_partition=0 "
        "export_path=" + output_path)
    IJ.run("Collect Garbage")
    print("BDV exported: " + output_path)


## 5. TrackMate ; overlap tracker

def run_trackmate(imp, channel, min_iou, scale_factor, iou_method):
    print('Starting TrackMate...')
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
    IJ.run("Collect Garbage")
    return tm, model


## 6. export xml TM

def save_trackmate_xml(model, settings_obj, path):
    writer = TmXmlWriter(File(path), Logger.IJ_LOGGER)
    writer.appendModel(model)
    writer.appendSettings(settings_obj)
    writer.writeToFile()
    print("TrackMate XML saved: " + path)


## 7. export labeling image

def export_label_image(trackmate, imp_ref, path):
    SelectionModel(trackmate.getModel())
    label_imp = LabelImgExporter.createLabelImagePlus(
        trackmate, False, False, LabelIdPainting.LABEL_IS_TRACK_ID)
    label_imp.setCalibration(imp_ref.getCalibration())
    IJ.saveAsTiff(label_imp, path)
    label_imp.close()
    IJ.run("Collect Garbage")
    print("Label image saved: " + path)


# main

def main():
    imp_orig   = open_czi(str(myInputFile))
    #imp_r      = reslice_and_swap(imp_orig, spacingZ)
    imp_r = imp_orig
    close_original(imp_orig)
    export_bdv(imp_r, str(myOutputDir) + "/" + outputName)
    tm, model  = run_trackmate(imp_r, detectorChannel, minIoU, scaleFactor, iouMethod)
    save_trackmate_xml(model, tm.getSettings(), str(myOutputDir) + "/" + outputName + "_trackmate.xml")
    export_label_image(tm, imp_r, str(myOutputDir) + "/" + outputName + "_labels.tif")
    print("Done.")

main()