# Notebooks for ```pyLINEAR```


## Abstract

This is a collection of notebooks to demonstrate most of the functionality of ```pyLINEAR``` v2.0.  


## Notebooks
The notebooks have been constructed with a certain goal and to be done in a specific order:

|    | Notebook | Content | 
|----|----------|---------|
| 1  | ```pylinear_synthetic_images.ipynb``` | Create the direct image and segmentation map necessary for later notebooks. | 
| 2  | ```pylinear_simulate_grism.ipynb``` | Simulate grism images for *simple sources*: sources with a single spectrum (in contrast to *composite sources* which have mutliple spectra). | 
| 3  | ```pylinear_extract_simple.ipynb``` | Extract the simple sources from the previous notebook. |
| 4  | ```pylinear_composite.ipynb``` | Simulate and Extract composite sources. |
| 5  | ```pylinear_wfc3ir_data.ipynb``` | Extract real WFC3/IR observations in G102. |


## Requirements

The ```setup.py``` should install all of the python requirements, however there are a few things that I find very helpful that are outside of python. Namely:

| package | purpose | location |
|---------|---------|----------|
| ds9     | view fits files | [https://sites.google.com/cfa.harvard.edu/saoimageds9](https://sites.google.com/cfa.harvard.edu/saoimageds9) |
| HDFView | GUI to view HDF5 files (```pyLINEAR``` stores intermediate products as HDF5 files) | [https://www.hdfgroup.org/downloads/hdfview/](https://www.hdfgroup.org/downloads/hdfview/) |

*Note* HDFView is free, however you will need to register with the HDFGroup.



## Command-Line Interface

```pyLINEAR``` has a convenient command-line interface (CLI) for most broad operations.  You can see the allowable inputs with:

```prompt> pylinear -h```

After having gone through the notebooks, many of these variables should be familiar.  Broadly speaking, the functionality illustrated in the notebooks is  implemented by a single call to the CLI.  

The inputs to the CLI can be given one-by-one, or by a configuration file.  Instead of describing the file, it's maybe easier to just dump the config file and look at it.  If you have questions, email me: [rryan@stsci.edu](mailto:rryan@stsci.edu?subject=[GitHub]%20PyLINEAR%20notebooks).


```prompt> pylinear -d pylinear_example.cfg```

Then the config can be used with the command:

```prompt> pylinear -c pylinear_example.cfg```


