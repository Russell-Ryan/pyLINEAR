import numpy as np


# settings for writing HDF5 files.  See h5py documentation for the 
# description of these terms
COMPARGS = {'compression':'gzip','compression_opts':9}


# data tyep for segmentation IDs.  Permit negative segid
# to encode (x,y) ID for IFU-like object (maybe make this a float)
SEGTYPE = np.int32
