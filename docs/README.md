# FAQs

### What is the format of the obs.lst file?
*This should be an ascii file with two columns (space delimited).  The first column should be the full path to a direct image (i.e. mosaicked image).  The second column should specify the filter, serialized as TELESCOPE\_INSTRUMENT\_FILTER (e.g. hst\_wfc3\_f105w).*

```
f105w_drz.fits    hst_wfc3_f105w
f160w_drz.fits    hst_wfc3_f160w
f125w_drz.fits    hst_wfc3_f125w
```
*If only one row is specified, then the initial guess of the spectrum will be set by assuming f<sub>&lambda;</sub> equal to the brightness measured in the one row.  If multiple rows are specified, then the initial spectrum is interpolated from the collection of photometry.  __In either case, the image in the first row specifies the extraction weights.__*

*I have provided a few broadband filters commonly used with HST/ACS and HST/WFC3, they are specified in [pylinear/synthphot/filters.py](https://github.com/Russell-Ryan/pyLINEAR/blob/master/pylinear/synthphot/filters.py "filters.py").  It is trivial to update this file and include additional files.*

---


### What is the format of the sed.lst file?

*This should be an ascii file with three columns (space delimited).  The first column should be an integer corresponding to a segmentation ID in the specified in the ```segmap``` in the yaml configuration file.  The second column specifies a full path to an ascii file  that contains the spectrum.  These files should also be space-delimited ascii files of &lambda; (in A) and f<sub>&lambda;</sub> (in arbitrary units).  The third column should be redshift.*

```
1   sed1.ascii       0.0
2   another.ascii    0.2
541 final_sed.ascii  0.221244211
```
*The spectra will be normalized based on the brightness measured in the obs.lst file above.*

---

### What about noise in the simulated images?

*We made the decision to omit the noise calculations, figuring that each instrument would be sufficiently different and we were not experts on every instrument.  I am tinkering with some general noising strategies, but they are extremely experimental at this point.*

*The simulated images will have an uncertainty array set to unity (floating-point) and a data-quality array set to zero (unsigned integer).  These can be simply modified by whatever noise strategy you see fit; I would recommend this for the (re-)extraction to make sense. __Stay tuned if you want my noise strategies.__*

---


