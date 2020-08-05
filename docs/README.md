# FAQs

[How to prepare the FLTs for extraction?](#how-to-prepare-the-flts-for-extraction)  
[What is the format of the obs.lst file?](#what-is-the-format-of-the-obslst-file)  
[What is the format of the sed.lst file?](#what-is-the-format-of-the-sedlst-file)  
[What is the format of the wcs.lst file?](#what-is-the-format-of-the-wcslst-file)  
[What about noise in the simulated images?](#what-about-noise-in-the-simulated-images)  
[astropy.wcs.wcs Convergence error?](#astropywcswcs-convergence-error)

---



### How to prepare the FLTs for extraction?

*The FLTs should have at least two post-processing steps that are __not__ performed by pylinear in any capacity:*

*__1. Background subtraction:__ The standard approach is to subtract "master sky" image(s), which are based on a particular spectral component in the sky spectrum.  For WFC3/IR, [Pirzkal & Ryan (2017)](http://www.stsci.edu/hst/wfc3/documents/ISRs/WFC3-2017-05.pdf). have developed approaches for dealing with multiple spectral components that (potentially vary with time), which is available on [GitHub](https://github.com/npirzkal/HeI_IMA/blob/master/HeI_IMA.py).  But see also [Brammer, Ryan, & Pirzkal (2015)](http://www.stsci.edu/hst/wfc3/documents/ISRs/WFC3-2015-17.pdf), [Pirzkal (2014)](http://www.stsci.edu/hst/wfc3/documents/ISRs/WFC3-2014-11.pdf), and [Brammer,  N. Pirzkal, P. McCullough, J. MacKenty (2014)](http://www.stsci.edu/hst/wfc3/documents/ISRs/WFC3-2014-03.pdf) for a chronological account of this approach.*

*__2. Astrometric refinement:__ You will likely have pre-imaging associated with the grism spectroscopy, which can be used to align to an existing mosiac.  This is most commonly done with [TweakReg](https://drizzlepac.readthedocs.io/en/latest/tweakreg.html).*



[Back to the top](#faqs)

---

### What is the format of the obs.lst file? 
*This should be an ascii file with two columns (space delimited).  The first column should be the full path to a direct image (i.e. mosaicked image).  The second column should specify the filter, serialized as TELESCOPE\_INSTRUMENT\_FILTER (e.g. hst\_wfc3\_f105w).*

```
# 1: full path to direct image
# 2: serialized filter curve name

f105w_drz.fits    hst_wfc3_f105w
f160w_drz.fits    hst_wfc3_f160w
f125w_drz.fits    hst_wfc3_f125w
```
*If only one row is specified, then the initial guess of the spectrum will be set by assuming a flat f<sub>&lambda;</sub> equal to the brightness measured in the one row.  If multiple rows are specified, then the initial spectrum is interpolated from the collection of photometry.  __In either case, the image in the first row specifies the extraction weights.__*

*I have provided a few broadband filters commonly used with HST/ACS and HST/WFC3, they are specified in [pylinear/synthphot/filters.py](https://github.com/Russell-Ryan/pyLINEAR/blob/master/pylinear/synthphot/filters.py "filters.py").  It is trivial to update this file and include additional files.*

[Back to the top](#faqs)

---


### What is the format of the sed.lst file?

*This should be an ascii file with three columns (space delimited).  The first column should be an integer corresponding to a segmentation ID in the specified in the ```segmap``` in the yaml configuration file.  The second column specifies a full path to an ascii file  that contains the spectrum.  These files should also be space-delimited ascii files of &lambda; (in Å) and f<sub>&lambda;</sub> (in arbitrary units).  The third column should be redshift.*

```
# 1: Object ID
# 2: spectrum file

1   sed1.ascii      
2   another.ascii    
541 final_sed.ascii  
```
*The spectra will be normalized based on the brightness measured in the obs.lst file above.*

[Back to the top](#faqs)

---

### What is the format of the wcs.lst file?

*The wcs.lst file specifies the basic properties of an observation that you wish to simulate.  We have tried to make this very user-friendly, by thinking "like an astronomer."  Therefore, this is an ascii file with five columns: (1) the base name of the file, (2) the CRVAL1 (in deg), (3) the CRVAL2 (in deg), (4) the ORIENTAT (just the traditional position angle in deg as E of N), and (5) grism.  But there are four required header keywords that specify the Telescope, Instrument, Detector, and Blocking filter (**NOTE** the blocking-filter concept is mostly for JWST and HST/Roman instruments will have ```BLOCKING = ```).  For example, for WFC3-IR:*

```
# TELESCOPE = HST
# INSTRUMENT = WFC3
# DETECTOR = IR
# BLOCKING = 

1    53.122751   -27.805089    0.
2    53.122751   -27.805089    10.
```

*This would create two images (1_flt.fits and 2_flt.fits) whose centers are given by the middle two columns and a position angle by the final column.*



[Back to the top](#faqs)

---

### What about noise in the simulated images?

*We made the decision to omit the noise calculations, figuring that each instrument would be sufficiently different and we were not experts on every instrument.  I am tinkering with some general noising strategies, but they are extremely experimental at this point.*

*The simulated images will have an uncertainty array set to unity (floating-point) and a data-quality array set to zero (unsigned integer).  These can be simply modified by whatever noise strategy you see fit; I would recommend this for the (re-)extraction to make sense. __Stay tuned if you want my noise strategies.__*

### astropy.wcs.wcs Convergence error?

*You probably got an error like this:*

> astropy.wcs.wcs.NoConvergence: 'WCS.all_world2pix' failed to converge to the requested accuracy. After 1 iterations, the solution is diverging at least for one input point. 

*The likely explanation is that your segmentation map and direct image(s) are very far (in angular distance) from the FLTs you wish to extract.  If that doesn't help, let me know*

[Back to the top](#faqs)

---

