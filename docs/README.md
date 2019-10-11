# FAQs
1. [What is the format of the obs.lst file?](#what-is-the-format-of-the-obslst-file)
2. [What is the format of the sed.lst file?](#what-is-the-format-of-the-sedlst-file)
3. [What about noise in the simulated images?](#what-about-noise-in-the-simulated-images)
4. [How do I read the output HDF5 file containing the spectra?](#how-do-i-read-the-out-hdf5-file-containing-the-spectra)

---

### What is the format of the obs.lst file? 
*This should be an ascii file with two columns (space delimited).  The first column should be the full path to a direct image (i.e. mosaicked image).  The second column should specify the filter, serialized as TELESCOPE\_INSTRUMENT\_FILTER (e.g. hst\_wfc3\_f105w).*

```
f105w_drz.fits    hst_wfc3_f105w
f160w_drz.fits    hst_wfc3_f160w
f125w_drz.fits    hst_wfc3_f125w
```
*If only one row is specified, then the initial guess of the spectrum will be set by assuming a flat f<sub>&lambda;</sub> equal to the brightness measured in the one row.  If multiple rows are specified, then the initial spectrum is interpolated from the collection of photometry.  __In either case, the image in the first row specifies the extraction weights.__*

*I have provided a few broadband filters commonly used with HST/ACS and HST/WFC3, they are specified in [pylinear/synthphot/filters.py](https://github.com/Russell-Ryan/pyLINEAR/blob/master/pylinear/synthphot/filters.py "filters.py").  It is trivial to update this file and include additional files.*

[Back to the top](#faqs)

---


### What is the format of the sed.lst file?

*This should be an ascii file with three columns (space delimited).  The first column should be an integer corresponding to a segmentation ID in the specified in the ```segmap``` in the yaml configuration file.  The second column specifies a full path to an ascii file  that contains the spectrum.  These files should also be space-delimited ascii files of &lambda; (in A) and f<sub>&lambda;</sub> (in arbitrary units).  The third column should be redshift.*

```
1   sed1.ascii       0.0
2   another.ascii    0.2
541 final_sed.ascii  0.221244211
```
*The spectra will be normalized based on the brightness measured in the obs.lst file above.*

[Back to the top](#faqs)

---

### What about noise in the simulated images?

*We made the decision to omit the noise calculations, figuring that each instrument would be sufficiently different and we were not experts on every instrument.  I am tinkering with some general noising strategies, but they are extremely experimental at this point.*

*The simulated images will have an uncertainty array set to unity (floating-point) and a data-quality array set to zero (unsigned integer).  These can be simply modified by whatever noise strategy you see fit; I would recommend this for the (re-)extraction to make sense. __Stay tuned if you want my noise strategies.__*

[Back to the top](#faqs)

---


### How do I read the output HDF5 file containing the spectra?

*First, let me justify the use of a new file format that might be foriegn to many astronomers.  __pylinear__, unlike the IDL implementation, is capable of "grouping" sources. I define "grouping" as:*

> **grouping:** the process of identifying the sources whose extraction orders overlap in the dispersed images.  
> 
> The groups are themselves grouped, and represent the smallest atomic unit to extract and fully encapsulate the contamination present in the data.

*Since the groups are individual sets of spectral extraction, they have their unique metadata and results.  For example, if you do a golden-search optimization, then they will each have a unique values (&chi;<sup>2</sup>, matrix norm, etc.).  Therefore I needed a file format that would allow for this grouped/hierarchical structure, and settled on HDF5 (but perhaps in the future move to something like [ASDF](https://pypi.org/project/asdf/)).  For quick viewing and basic editting of HDF5 files, please consider the [HDFView](https://www.hdfgroup.org/downloads/hdfview/) produced by the HDF Group (this program is free to download, but does require you register).* 

*Ok, back to the question you asked.  I have a simple class in pylinear.extraction module, called [SEDFile](https://github.com/Russell-Ryan/pyLINEAR/blob/master/pylinear/modules/extraction/sedfile.py), that facilitates many operations with these files (reading spectra, group metadata, simple plots, etc.).  So here's an example to read every source and make a quick plot:*

```
import matplotlib.pyplot as plt
import pylinear.modules.extraction.sedfile as sedfile

myFile='myOutputFile.h5'
with sedfile.SEDFile(myFile) as sd:
    for segid in sd.segIDs:
        data=sd.spectrum(segid)
        plt.plot(data['lam'],data['flam'],label='{}'.format(segid))
        plt.tight_layout()
        plt.show()
```

*Just change the name of the ```myFile``` variable.  I hope this helps, but if you have more questions, then let me know!*  


>**An outro note:** The grouping can be controled by the ```group``` keyword in the configuration file.


[Back to the top](#faqs)


