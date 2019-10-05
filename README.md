# pylinear

This is a python implementation of the LINEAR algorithm for extracting slitless spectroscopy from HST/WFC3-IR as developed by [Ryan, R. E., Jr.; Casertano, S.; Pirzkal, N. 2018, PASP, 130, 4501](https://ui.adsabs.harvard.edu/abs/2018PASP..130c4501R/abstract).  The LINEAR software was originally developed in IDL and C, but had several limitations that were remedied in the porting to Python.

For any questions or comments, please contact [Russell Ryan](mailto:rryan@stsci.edu?subject=[GitHub]%20PyLINEAR%20question).

## Requirments

pylinear is written for python 3.7.  I recommend installing this with STScI [miniconda](https://astroconda.readthedocs.io/en/latest/).  Let me know if you have questions about this.

## Installation

The installation is now down entirely via pip.

```
pip install git+https://github.com/russell-ryan/pylinear 
```
This will install and compile all of the dependencies for pylinear.  Just for the record this will get

| Package                    | Description |
|----------------------------|-------------|
| [h5axeconfig](https://github.com/Russell-Ryan/h5axeconfig) | Does basic processing with the grism configuration |
| [h5py](https://pypi.org/project/h5py/) | Most of the output files are in [HDF5](https://www.hdfgroup.org/solutions/hdf5/) format, so you'll need this |
| [ruamel.yaml](https://pypi.org/project/ruamel.yaml/) | For reading and working with configuration data |
| [wget](https://pypi.org/project/wget/) | For downloading data from the web|
| [emcee](https://github.com/dfm/emcee) | For the MCMC simulations to compute error bars |
| [shapely](https://pypi.org/project/Shapely/) | For some cool geometry things|


### Helpful Suggestion:

Since pylinear outputs the spectroscopy in an HDF5 file, you might want a user-friendly interface to inspect an HDF5 file.  I recommend the [HDF Viewer](https://www.hdfgroup.org/downloads/hdfview/), which is free to download (but you will need to register with HDFgroup).



## Test Scripts

I currently do not have test scripts for pylinear, but the subsystems that I developed (h5axeconfig and polyclip) do have test scripts. 

```
TBD

```



## Documentation

* LINEAR publication: [Ryan, Casertano, & Pirzkal (2018)](https://ui.adsabs.harvard.edu/abs/2018PASP..130c4501R/abstract)
* IDL version regarding the implemention: [Ryan, Casertano, \& Pirzkal (2018)](http://www.stsci.edu/hst/wfc3/documents/ISRs/WFC3-2018-13.pdf)
* YAML (Yet Another Markup Language) usage: [https://yaml.org](https://yaml.org)


## Citations

If you find this code useful, please cite our work at: [Ryan, R. E., Jr.; Casertano, S.; Pirzkal, N. 2018, PASP, 130, 4501](https://ui.adsabs.harvard.edu/abs/2018PASP..130c4501R/abstract)


