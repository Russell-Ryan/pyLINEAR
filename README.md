# pyLINEAR 
[![Build Status](https://travis-ci.org/Russell-Ryan/pyLINEAR.svg?branch=master)](https://travis-ci.org/Russell-Ryan/pyLINEAR) [![DOI](https://zenodo.org/badge/193565310.svg)](https://zenodo.org/badge/latestdoi/193565310)



## Abstract

his is a python implementation of the LINEAR algorithm for extracting slitless spectroscopy from HST/WFC3-IR as developed by [Ryan, R. E., Jr.; Casertano, S.; Pirzkal, N. 2018, PASP, 130, 4501](https://ui.adsabs.harvard.edu/abs/2018PASP..130c4501R/abstract).  The LINEAR software was originally developed in IDL and C, but had several limitations that were remedied in the porting to Python.

For any questions or comments, please contact [Russell Ryan](mailto:rryan@stsci.edu?subject=[GitHub]%20PyLINEAR%20question).



## Installation

*pylinear* is developed with python 3.7.  I recommend installing this with STScI [miniconda](https://astroconda.readthedocs.io/en/latest/).  Let me know if you have questions about this.


### Reference Files
You will need to get the reference files from: [my Box link](https://stsci.app.box.com/folder/119486568677).  Unpack these files in separate directory and set the environment variable:

``` export PYLINEAR_CONFIG=/FULL/PATH/TO/THE/DIRECTORY/ ```





### Python Dependencies



``` pip install . -r requirements.txt ```


The installation is now down entirely via pip.

| Package | Purpose | install |
|---------|---------|---------|
| [h5py](https://pypi.org/project/h5py/) | read/write HDF5 files | ```pip install h5py``` |
| [emcee](https://github.com/dfm/emcee) | MCMC simulation toolkit | ``` pip install emcee``` |
| [shapely](https://pypi.org/project/Shapely/) | operations with shapes | ```pip install shapely``` |
| [fitsimage](https://github.com/Russell-Ryan/fitsimage) | basic operations on astronomical images with headers | clone from git |
| [polyclip](https://github.com/Russell-Ryan/polyclip) | python class for polygon clipping | clone from git |
| [colorlog](https://github.com/Russell-Ryan/colorlog) | logging class to use colors and stdout | clone from git |


> **Helpful Tip:** Since *pylinear* outputs intermediate data prodcuts in HDF5 files, you might want a user-friendly interface to inspect an HDF5 file.  I recommend [HDFView](https://www.hdfgroup.org/downloads/hdfview/), which is free to download (but you will need to register with HDFgroup).




## Documentation



* LINEAR publication: [Ryan, Casertano, & Pirzkal (2018)](https://ui.adsabs.harvard.edu/abs/2018PASP..130c4501R/abstract)
* IDL version regarding the implemention: [Ryan, Casertano, \& Pirzkal (2018)](http://www.stsci.edu/hst/wfc3/documents/ISRs/WFC3-2018-13.pdf)


### Citations

If you find this code useful, then we kindly ask that you cite our work: [Ryan, R. E., Jr.; Casertano, S.; Pirzkal, N. 2018, PASP, 130, 4501](https://ui.adsabs.harvard.edu/abs/2018PASP..130c4501R/abstract)


### Frequent Errors:

Error message:
> astropy.wcs.wcs.NoConvergence: 'WCS.all_world2pix' failed to converge to the requested accuracy.
After 1 iterations, the solution is diverging at least for one input point.
Likely explanation:

*The segmentation map is likely far (in angular distance) from the FLTs in question.*