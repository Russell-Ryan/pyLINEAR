# List of Items To-Do or Fix.

1.  update how FITS headers are written when using the individual subroutines.  The contents are always the defaults, as they just use the ```config.Config().update_header(hdr)```.  So could just update ```config.Config()``` with each call.  
2. check how ```colorlog.ColorLog()``` is affecting ```stderr```.  The progressbar ```tqdm.tqdm()``` seems to use ```stderr```.
3. investigate if ```colorlog.ColorLog``` is also affecting how printing is done in Jupyter.

4. change out ```grism.config.Beam``` is loaded.  so if no data is valid that the beam is returned as ```None```.  Use the ```__new__()``` classmethod.
