import os
import numpy as np
from collections import OrderedDict
import h5py

from h5axeconfig import utils as h5utils

from pylinear.utilities import asciitable
from . import simulated,observed

class Data(object):
    ''' a class to hold the grism data info '''

    def __init__(self,filename,filetype,conffile):
        self.filename=filename
        self.filetype=filetype
        self.grism=None
        
        # the grism images
        self.images=OrderedDict()

        
        # process the file type
        if self.filetype=='img':
            self.loadObserved(self.filename,conffile)
        elif self.filetype=='wcs':
            self.loadSimulated(self.filename,conffile)
        else:
            raise NotImplementedError("{} unsupported.".format(filetype))
        print('[info]Loaded {} grism images.\n'.format(len(self)))
        
        
    def __contains__(self,key):
        return key in self.sources 
        
    def __len__(self):
        return len(self.images)
        
    def __str__(self):
        t='{} grism images: \n'.format(str(len(self.images)))
        for k,v in self.images.items():
            t=t+'{:>8} {}\n'.format(v.filetype,v.filename)
        return t

    def __iter__(self):
        yield from self.images.items()

    @property
    def values(self):
        return list(self.images.values())
        
    def loadObserved(self,filename,conffile):
        print('[info]Loading observed grism images')

        
        exts=h5utils.detectorData(conffile,'science_ext','extver')

        
        # read the data
        table=asciitable.AsciiTable(['filename'],filename=filename)
        grism=[]
        for thisFile in table:
            image=observed.ObservedGrism(thisFile,exts)
            grism.append(image.keyword('filter'))
            
            # record the image
            self.images[image.dataset]=image
        if len(set(grism))==1:
            self.grism=grism[0]
        else:
            raise RuntimeError("Images are of different grisms")

            
    def loadSimulated(self,filename,siaffile):
        
        print('[info]Loading simulated grism images')

        columns=['dataset','crval1','crval2','orientat']
        table=asciitable.AsciiTable(columns,filename=filename)
        for dataset,crval1,crval2,orientat in table:
            dataset=str(dataset)
            crvals=(crval1,crval2)
            image=simulated.SimulatedGrism(dataset,crvals,orientat,siaffile)

            # record the image
            self.images[dataset]=image
            
