import numpy as np
from scipy.spatial import ConvexHull

from .extractionparameters import ExtractionParameters
from pylinear.synthphot import SED
from pylinear.astro import WCS

class Source(WCS,ExtractionParameters):
    def __init__(self,img,seg,zero,segid=None,lamb0=None,lamb1=None,dlamb=None):

        #get the SEGID
        if segid is None:
            try:
                segid=seg.header['SEGID']
            except:
                raise RuntimeError("Segmentation ID is missing from header.")
        self.segid=segid

        # get the good pixels
        g=np.where(seg.data == self.segid)
        self.npix=len(g[0])
        if self.npix==0:
            print("[warn]No valid pixels for source={}".format(self.npix))

            
        # check that the img/seg astrometry matches
        keys=['NAXIS','NAXIS2','CRPIX1','CRPIX2','CRVAL1','CRVAL2', \
              'CD1_1','CD1_2','CD2_1','CD2_2','CTYPE1','CTYPE2']
        ok=[img[key]==seg[key] for key in keys]
        if False in ok:
            raise RuntimeError("Incompatible img/seg fits header keywords.")
        
        # initialize an SED object
        self.sed=SED()
        
        # initialize the header
        WCS.__init__(self,seg.header)  # could be seg or img here
        
        # initialize the extraction parameters
        ExtractionParameters.__init__(self,lamb0,lamb1,dlamb)

        # compute the area of this source
        self.area=self.npix*self.pixelarea

        # recall that Python & IDL are inverted
        self.xd=g[1]      # direct image x-coordinates
        self.yd=g[0]      # direct image y-coordinates

        # compute a few brightness measures
        self.total=np.sum(img.data[g])
        if self.total >0:
            self.mag=-2.5*np.log10(self.total)+zero
            self.wht=img.data[g]/self.total

            # compute the centroids (in pixel and RA,Dec)
            self.xyc=np.array([np.average(self.xd,weights=self.wht), \
                               np.average(self.yd,weights=self.wht)])
            self.adc=np.array(self.xy2ad(self.xyc[0],self.xyc[1]))
            
        

        
    def instrumentalFlux(self,img):
        ''' compute the instrumental flux of this source in an image '''
        xd=self.xd-int(self.ltv[0])
        yd=self.yd-int(self.ltv[1])
        tot=np.sum(img.data[yd,xd])
        return tot

    @property
    def convexHull(self):
        points=np.array([self.xd,self.yd]).T
        hull=ConvexHull(points)

        xh,yh=[],[]
        for vertex in hull.vertices:
            xh.append(points[vertex,0])
            yh.append(points[vertex,1])
        xh,yh=np.array(xh),np.array(yh)

        return xh,yh

    
    @property
    def name(self):
        return '{}'.format(self.segid)
    

    def __str__(self):
        return 'Source segid={}'.format(self.segid)

    def __iter__(self):
        for x,y,w in zip(self.xd,self.yd,self.wht):
            yield x,y,w
