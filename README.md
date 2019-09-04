# PyLinear

This is a python implementation of the LINEAR algorithm for extracting slitless spectroscopy from HST/WFC3-IR as developed by [Ryan, R. E., Jr.; Casertano, S.; Pirzkal, N. 2018, PASP, 130, 4501](https://ui.adsabs.harvard.edu/abs/2018PASP..130c4501R/abstract).  The LINEAR software was originally developed in IDL and C, but had several limitations that were remedied in the porting to Python.

For any questions or comments, please contact [Russell Ryan](mailto:rryan@stsci.edu?subject=[GitHub]%20PyLINEAR%20question).


## Installation
pyLINEAR requires several packages that exist in the ether, as well as several that I wrote.  Here is a complete description of how to install, and the order.

1. install [polycilp](https://github.com/Russell-Ryan/polyclip)
```
git clone https://github.com/Russell-Ryan/polyclip.git
cd polyclip
python setup.py install
```


2. install [h5axeconfig](https://github.com/Russell-Ryan/h5axeconfig).  This has three key dependences that must be resolved first: [h5py](https://pypi.org/project/h5py/), [ruamel](https://pypi.org/project/ruamel.yaml/), and [wget](https://pypi.org/project/wget/).

```
pip install h5py
pip install wget
pip install ruamel.yaml
```

Then clone and install h5axeconfig

```
git clone https://github.com/Russell-Ryan/h5axeconfig.git
cd h5axeconfig
python setup.py install
```

3. install pyLINEAR.  This has two key dependencies not yet resolved: [emcee](https://github.com/dfm/emcee) and [shapely](https://pypi.org/project/Shapely/)
```
git clone https://github.com/dfm/emcee.git
cd emcee
python setup.py install
pip install shapely
```

Then clone and install pyLINEAR
```
git clone https://github.com/Russell-Ryan/pyLINEAR.git
cd pyLINEAR
python setup.py install
```

**pyLINEAR also uses the [h5py](https://pypi.org/project/h5py/) library, but this should now be installed.**

4. Hopefully at this point, everything should be working --- including the compiled C components.



## Example Usage
```

TBD

```



## Documentation


* LINEAR publication: [Ryan, Casertano, & Pirzkal (2018)](https://ui.adsabs.harvard.edu/abs/2018PASP..130c4501R/abstract)
* IDL version regarding the implemention: [Ryan, Casertano, \& Pirzkal (2018)](http://www.stsci.edu/hst/wfc3/documents/ISRs/WFC3-2018-13.pdf)
* YAML (Yet Another Markup Language) usage: [https://yaml.org](https://yaml.org)



## Citations

If you find this code useful, please cite our work at: [Ryan, R. E., Jr.; Casertano, S.; Pirzkal, N. 2018, PASP, 130, 4501](https://ui.adsabs.harvard.edu/abs/2018PASP..130c4501R/abstract)

