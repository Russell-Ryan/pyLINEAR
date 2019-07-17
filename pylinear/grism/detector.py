from astropy.io import fits


from pylinear.astro import WCS


class Detector(WCS):
    ''' Class to hold a given detector --- camera has many detectors '''

    def __init__(self,hdr):
        self.hdr=hdr
        WCS.__init__(self,self.hdr)
    

    def __str__(self):
        return 'grism image detector'

    
    @property
    def npix(self):
        return int(self.naxis[0]*self.naxis[1])
    
