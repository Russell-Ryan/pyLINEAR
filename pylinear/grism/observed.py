
from astropy.io import fits

import h5axeconfig

from .grismimage import GrismImage
from .detector import Detector


class ObservedGrism(GrismImage):
    filetype='observed'


    # must pass extensions into this
    def __init__(self,fileName,exts):
        GrismImage.__init__(self,fileName,filename=True)
        
        # read the PHDU
        with fits.open(self.filename) as hdul:
            self.phdu=hdul[0].header

            for detname,exten in exts.items():
                hdr=hdul[exten].header
                
                self.detectors[detname]=Detector(hdr)
                
                
    @property
    def primaryHeader(self):
        with fits.open(self.filename) as hdul:
            hdr=hdul[0].header
        return hdr
                

    def readfits(self,extname,extver):
        with fits.open(self.filename) as hdul:
            hdu=hdul[(extname,extver)]
            dat,hdr=hdu.data,hdu.header

        return dat,hdr
        
