from astropy.io import fits

import numpy as np

from pylinear.wcs import WCS
from pylinear.utilities import indices

class Detector(WCS):
    ''' Class to hold a given detector --- camera has many detectors '''

    def __init__(self,hdr):
        self.hdr=hdr
        self.shape=(int(hdr['NAXIS2']),int(hdr['NAXIS1']))
        WCS.__init__(self,self.hdr)
        self.bpx=[]
        

    def __str__(self):
        return 'grism image detector'

    
    @property
    def npix(self):
        #return int(self.naxis[0]*self.naxis[1])
        return self.shape[1]*self.shape[0]
    

    def extendBPX(self,bpx):
        self.bpx.extend(bpx)

    def applyBPX(self,img,DQAval=1):
        if len(self.bpx) != 0:
            xg,yg=indices.one2two(self.bpx,self.shape)
            img[yg,xg]=1
            
            
