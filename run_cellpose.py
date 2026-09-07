from cellpose import models
from cellpose.io import imread
import numpy as np
#import matplotlib.pyplot as plt
from cellpose import models, io

io.logger_setup()

model = models.CellposeModel(gpu=True)

# list of files
# PUT PATH TO YOUR FILES HERE!
files = ['/Users/theresaswayne/Desktop/input/merged input/all_chans/']

channels = [[0,0]] # This means we are processing single-channel greyscale images.

#imgs = [imread(f) for f in files]
#nimg = len(imgs)


for i in files:
	image = io.imread(i)
	masks, flows, styles = model.eval(image)
	io.save_rois(masks, i)

#masks, flows, styles = model.eval(imgs)

# img = imread("img.tif") # tiff is n x 100 x 100

# if there is only one channel
# TODO fix this imgs_cp = imgs[0,0] # read as single channel
#channels = [[0,0]] # This means we are processing single-channel greyscale images.


# if nuclei and cytoplasm are in first two channels
# img_cp = img[:2] # keep first two channels

# if nuclei and cytoplasm are in different channels from first two
# img_cp = img[[1, 3]] # keep 1 and 3 (2nd and 4th channels)

# if you want to combine two stains to create your "cytoplasm" channel
# in this example indices 0 and 2 (1st and 3rd) have two cellular stains
# and nuclei are in index 1 (2nd channel)
#imgs = np.stack((img[[0,2]].sum(axis=0), img[1]), axis=0)

#masks, flows, styles = model.eval(img_cp)







