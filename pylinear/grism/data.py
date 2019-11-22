import os
import numpy as np
import pdb
import h5py

from h5axeconfig import utils as h5utils

from pylinear.utilities import asciitable
from . import simulated,observed

class Data(dict):
    ''' a class to hold the grism data info '''

    def __init__(self,filename,filetype,conffile):
        self.filename=filename
        self.filetype=filetype
        self.grism=None
        
        # the grism images
        #self.images=OrderedDict()

        # process the file type
        if self.filetype=='img':
            self.loadObserved(self.filename,conffile)
        elif self.filetype=='wcs':
            self.loadSimulated(self.filename,conffile)
        else:
            raise NotImplementedError("{} unsupported.".format(filetype))
        print('[info]Loaded {} grism images.\n'.format(len(self)))
        
        
    #def __contains__(self,key):
    #    return key in self.sources 
        
    #def __len__(self):
    #    return len(self.images)
        
    def __str__(self):
        t='{} grism images: \n'.format(str(len(self)))
        for k,v in self.items():
            t=t+'{:>8} {}\n'.format(v.filetype,v.filename)
        return t

    #def __getitem__(self,k):
    #    return self.images[k]
    
    #def __iter__(self):
    #    yield from self.items()

    @property
    def datasets(self):
        return list(self.keys())

    @property
    def images(self):
        return list(self.values())
        
    #@property
    #def values(self):
    #    #return list(self.images.values())
    #    return list(self.values())
        
    def loadObserved(self,filename,conffile):
        print('[info]Loading observed grism images')

        beamfile=conffile['h5conf']
        exts=h5utils.detectorData(beamfile,'science_ext','extver')
        
        
        # read the data
        table=asciitable.AsciiTable(['filename'],filename=filename)
        grism=[]
        for thisFile in table:
            image=observed.ObservedGrism(thisFile,exts)
            grism.append(image.keyword('filter'))
            
            # record the image
            #self.images[image.dataset]=image
            self[image.dataset]=image
        if len(set(grism))==1:
            self.grism=grism[0]
        else:
            raise RuntimeError("Images are of different grisms")

            
    def loadSimulated(self,filename,conffile):
        
        print('[info]Loading simulated grism images')

        siaffile=conffile['h5siaf']
        
        columns=['dataset','crval1','crval2','orientat']
        table=asciitable.AsciiTable(columns,filename=filename)
        for dataset,crval1,crval2,orientat in table:
            dataset=str(dataset)
            crvals=(crval1,crval2)
            image=simulated.SimulatedGrism(dataset,crvals,orientat,siaffile)

            # record the image
            #self.images[dataset]=image
            self[dataset]=image
