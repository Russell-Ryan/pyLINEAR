import numpy as np
from astropy.io import fits
import os

from ..wcs import WCS
#from .siaf import SIAF
from .config import Beam
#from .instruments import load_detector

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

        self.conffile=device.grism_config(grism)

        # record teh defalts from the XML data
        self.defaults={'lamb0':device.grisms[grism].lamb0,
                       'lamb1':device.grisms[grism].lamb1,
                       'dlamb':device.grisms[grism].dlamb}
                       
        # save the extensions
        self.exten=device.extensions

        # save the bitmask
        self.bitmask=device.bitmask

        # save the sizes
        self.naxis1=np.uint32(self.hdr['NAXIS1'])
        self.naxis2=np.uint32(self.hdr['NAXIS2'])

        
    def load_beam(self,beam):
        return Beam(self.conffile,beam)

    
class SimulatedFile(GrismFile):
    TYPE='simulated'
    def __init__(self,obsconf,insconf):
        
        # initialize the parent
        detector=insconf[obsconf['instrument']][obsconf['detector']]
        grism=(obsconf['grism'],obsconf['blocking'])       
        GrismFile.__init__(self,detector,grism)

            
        # put some standard things in the header
        detector.header['TELESCOP']=(obsconf['telescope'],
                                     'telescope used to acquire data')
        detector.header['INSTRUME']=(obsconf['instrument'],
                                     'identifier for instrument used to acquire data')
        detector.header['DETECTOR']=(obsconf['detector'],
                                     'identifier for detector used to acquire data')
        detector.header['FILTER']=(obsconf['grism'],
                                   'element selected from filter wheel')
        #blocking=obsconf['blocking']
        #if blocking is None:
        #    blocking=' '
        #detector.header['BLOCKING']=(blocking,'blocking filter')
        if obsconf['blocking'] is not None:
            detector.header['BLOCKING']=(obsconf['blocking'],'blocking filter')
        detector.header['RA_APER']=(obsconf['crvals'][0],'Specified RA')
        detector.header['DEC_APER']=(obsconf['crvals'][1],'Specified Dec')
        detector.header['ORIENTAT']=(obsconf['orientat'],'Specified Orientat')
            
            
        #self.dataset=dataset
        self.dataset=obsconf['dataset']
        
        #self.detector.header.update_header(hdr)


        # get the reference siaf info
        refsiaf=detector[detector.refsiaf].siaf
        
        # do each device in the detector        
        for device in detector:

            # create an image
            img=SimulatedImage(obsconf['crvals'],obsconf['orientat'],
                               device,grism,refsiaf)
            #img=SimulatedImage(crvals,orientat,device,grism)
            
            # put some stuff into the header
            device.header.update_header(img.hdr)
                        
            # save the image
            self.images[device.name]=img
            
class SimulatedImage(GrismImage):
    TYPE='simulated'
    def __init__(self,crvals,orientat,device,grism,refsiaf):

        #obs=SIAF(device.siaf['telescope'],device.siaf['aperture'])
        #ref=SIAF(device.siaf['telescope'],device.siaf['reference'])

        #obssiaf=device.siaf
        hdr=device.siaf.make_header(*crvals,orientat,refsiaf=refsiaf)
        GrismImage.__init__(self,hdr,device,grism)

    def mkhdr(self,dtype,imgtype=None):
        hdr=super().mkhdr(dtype)
        if imgtype in self.exten:
            hdr['EXTNAME']=(self.exten[imgtype].extname,'extension name')
            hdr['EXTVER']=(self.exten[imgtype].extver,'extension version number')
        return hdr


    def add_background(self):
        return 0.0

    def make_uncertainty(self,sci):
        return np.full_like(sci,1.,dtype=self.exten['uncertainty'].dtype)

    
    
    
class ObservedFile(GrismFile):
    TYPE='observed'
    def __init__(self,filename,insconf):
        basename=os.path.basename(filename)
        self.dataset=basename.split(self.SUFFIX)[0]

        
        # get the primary header
        phdr=fits.getheader(filename,ext=0)

        # load the observational configuration and detector
        #obsconf=(phdr['TELESCOP'],phdr['INSTRUME'],phdr['DETECTOR'])
        #detector=load_detector(*obsconf)



        
        detector=insconf[phdr['INSTRUME']][phdr['DETECTOR']]
                         #grism=(obsconf['grism'],obsconf['blocking'])       
        
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
        ext=(device.extensions['science'].extname,
             device.extensions['science'].extver)
        hdr=fits.getheader(self.filename,ext=ext)
        GrismImage.__init__(self,hdr,device,grism)

    def readfits(self,exten):
        ext=(exten.extname,exten.extver)
        hdr=fits.getheader(self.filename,ext=ext)
        img=fits.getdata(self.filename,ext=ext)
        return img,hdr
    
    def load_science(self):
        return self.readfits(self.exten['science'])
    
    def load_uncertainty(self):
        return self.readfits(self.exten['uncertainty'])
    
    def load_dataquality(self):
        return self.readfits(self.exten['dataquality'])
