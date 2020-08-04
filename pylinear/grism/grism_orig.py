import numpy as np
from astropy.io import fits
import os

from ..wcs import WCS
from .siaf import SIAF
from .config import Beam
from .instruments import load_detector

class GrismFile(object):
    TYPE=''
    SUFFIX='_flt.fits'
    def __init__(self,detector,grism):
        self.images={}
        self.detector=detector
        self.grism=grism
        
    def __len__(self):
        return len(self.images)

    def __iter__(self):
        yield from self.images.values()

    def items(self):
        return self.images.items()

    def __getitem__(self,k):
        return self.images[k]

    @property
    def filename(self):
        return self.dataset+self.SUFFIX
    
class GrismImage(WCS):
    TYPE=''
    def __init__(self,hdr,device,grism):
        self.name=device.name

        self.hdr=hdr
        WCS.__init__(self,self.hdr)
        self.conffile=device.config_file(*grism)

        # save the extensions
        self.exten=device.exten

        # save the bitmask
        self.bitmask=device.bitmask

        # save the sizes
        self.naxis1=np.uint32(self.hdr['NAXIS1'])
        self.naxis2=np.uint32(self.hdr['NAXIS2'])

        
    def load_beam(self,beam):
        conf=Beam(self.conffile,beam)
        return conf

    
class SimulatedFile(GrismFile):
    TYPE='simulated'
    def __init__(self,dataset,crvals,orientat,grism,detector):
        GrismFile.__init__(self,detector,grism)

        # add the FILTER & Blocking combination to the header
        grate,block=grism     # the grating,blocking combination
        detector.header['FILTER']=(grate,'element selected from filter wheel')
        if block is not None:
            detector.header['BLOCKING']=(block,'blocking filter')

            
        self.dataset=dataset
        
        #self.detector.header.update_header(hdr)

        # do each device in the detector        
        for device in detector:

            # create an image
            img=SimulatedImage(crvals,orientat,device,grism)
            
            # put some stuff into the header
            device.header.update_header(img.hdr)
                        
            # save the image
            self.images[device.name]=img
            
class SimulatedImage(GrismImage):
    TYPE='simulated'
    def __init__(self,crvals,orientat,device,grism):
        obs=SIAF(device.siaf['telescope'],device.siaf['aperture'])
        ref=SIAF(device.siaf['telescope'],device.siaf['reference'])
        hdr=obs.make_header(crvals[0],crvals[1],orientat,refsiaf=ref)
        GrismImage.__init__(self,hdr,device,grism)


    def mkhdr(self,dtype,imgtype=None):
        hdr=super().mkhdr(dtype)
        if imgtype in self.exten:
            hdr['EXTNAME']=(self.exten[imgtype].name,'extension name')
            hdr['EXTVER']=(self.exten[imgtype].ver,'extension version number')
        return hdr


    def add_background(self):
        return 0.0


    
class ObservedFile(GrismFile):
    TYPE='observed'
    def __init__(self,filename):
        basename=os.path.basename(filename)
        self.dataset=basename.split(self.SUFFIX)[0]

        
        # get the primary header
        phdr=fits.getheader(filename,ext=0)

        # load the observational configuration and detector
        obsconf=(phdr['TELESCOP'],phdr['INSTRUME'],phdr['DETECTOR'])
        detector=load_detector(*obsconf)

        # get the grism element and blocking
        grism=(phdr.get('FILTER'),phdr.get('BLOCKING'))

        #initialize the grism file        
        GrismFile.__init__(self,detector,grism)

        # load each device in the detector        
        for device in detector:

            # create an image
            img=ObservedImage(filename,device,grism)

            # save the image
            self.images[device.name]=img
          

class ObservedImage(GrismImage):
    TYPE='observed'
    def __init__(self,filename,device,grism):
        self.filename=filename
        ext=(device.exten['science'].name,device.exten['science'].ver)
        hdr=fits.getheader(self.filename,ext=ext)
        GrismImage.__init__(self,hdr,device,grism)

    def readfits(self,exten):
        ext=(exten.name,exten.ver)
        hdr=fits.getheader(self.filename,ext=ext)
        img=fits.getdata(self.filename,ext=ext)
        return img,hdr
    
    def load_science(self):
        return self.readfits(self.exten['science'])
    
    def load_uncertainty(self):
        return self.readfits(self.exten['uncertainty'])
    
    def load_dataquality(self):
        return self.readfits(self.exten['dataquality'])
