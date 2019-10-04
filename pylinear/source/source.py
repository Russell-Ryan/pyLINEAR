import numpy as np
import scipy.ndimage as sn

from .direct import Direct
from .extractionparameters import ExtractionParameters

from pylinear.synthphot import SED
from pylinear.astro import WCS
from pylinear.utilities import convexhull



class Source(WCS,ExtractionParameters,Direct):
    SEGTYPE=np.uint32           # force SEGIDs to have this type

    def __init__(self,img,seg,zero,segid=None,lamb0=None,lamb1=None,dlamb=None,\
                 minpix=3,maglim=26,morph={}):
        
        #get the SEGID
        if segid is None:
            if 'SEGID' in seg.header:
                segid=seg.header['SEGID']
            else:
                #print('[warn]Segmentation ID is missing from header.')
                self.valid=False
                return
        self.segid=self.SEGTYPE(segid)


        # check that the img/seg astrometry matches
        keys=['NAXIS','NAXIS2','CRPIX1','CRPIX2','CRVAL1','CRVAL2', \
              'CD1_1','CD1_2','CD2_1','CD2_2','CTYPE1','CTYPE2']
        for key in keys:
            if img[key]!=seg[key]:
                #print('[warn]Incompatible headers for {}'.format(self.segid))
                self.valid=False
                return

        # these morphological operations restrict the number of pixels
        # that belong to the SEGmap that will be processed.
        if morph is not None:
            print('morphology')
            operations=[self.smooth,self.erode]
            for operation in operations:
                seg,img=operation(seg,img,morph)
        
        # get the good pixels
        g=np.where(seg.data == self.segid)
        self.npix=len(g[0])


        # check the number of pixels is large enough
        if self.npix<=minpix:
            #print('[warn]Too few pixels for {}.'.format(self.segid))
            self.valid=False
            return
                
        
        # initialize an SED object
        self.sed=SED()

        # initialize the header
        WCS.__init__(self,seg.header)  # could be seg or img here
        
        # initialize the extraction parameters
        ExtractionParameters.__init__(self,lamb0,lamb1,dlamb)

        # initialize the direct extraction
        Direct.__init__(self)



        # recall that Python & IDL are inverted
        self.xd=g[1]      # direct image x-coordinates
        self.yd=g[0]      # direct image y-coordinates
        
        
        # compute the area of this source
        self.area=self.npix*self.pixelarea


        # compute a few brightness measures
        self.total=np.sum(img.data[g])
        if self.total>0:
            self.mag=-2.5*np.log10(self.total)+zero
            if self.mag >maglim:
                #print('[warn]Below mag limit for {}'.format(self.segid))
                self.valid=False
                return
            
            self.wht=img.data[g]/self.total

            # compute the centroids (in pixel and RA,Dec)
            self.xyc=np.array([np.average(self.xd,weights=self.wht), \
                               np.average(self.yd,weights=self.wht)])
            self.adc=np.array(self.xy2ad(self.xyc[0],self.xyc[1]))

        elif self.total==0:
            #print('[warn]Zero flux for {}'.format(self.segid))
            self.valid=False
            return
        else:                
            #print('[warn]Negative flux for {}'.format(self.segid))
            self.valid=False
            return

        self.valid=True
            
        
    def instrumentalFlux(self,img):
        ''' compute the instrumental flux of this source in an image '''
        xd=self.xd-int(self.ltv[0])
        yd=self.yd-int(self.ltv[1])
        tot=np.sum(img.data[yd,xd])
        return tot


    
    @property
    def convexHull(self):
        return convexhull.vertices(self.xd,self.yd)
    
    @property
    def name(self):
        return '{}'.format(self.segid)
    

    def __str__(self):
        return 'Source segid={}'.format(self.segid)

    def __iter__(self):
        for x,y,w in zip(self.xd,self.yd,self.wht):
            yield x,y,w

    def __len__(self):
        return len(self.xd)



    #------- STUFF FOR THE MORPHOLOGICAL OPERATIONS ------
    

    def getValue(self,seg,morph,key):
        if key in seg:
            return seg[key]
        if key in morph:
            return morph[key]
        return None
    
    def smooth(self,seg,img,morph):
        key='FILTSIG'
        
        sig=self.getValue(seg,morph,key)
        if sig is None or sig <=0:
            return seg,img
        
        bad=seg.data != self.segid
        good=seg.data == self.segid
        V=img.data.copy()
        V[bad]=0
        VV=sn.gaussian_filter(v,sigma=sig)

        W=np.ones_like(img.data)
        W[bad]=0
        WW=sn.gaussian_filter(W,sigma=sig)
        Z=VV/WW
        img.data[good]=z[good]

        seg[key]=sig
        
        return seg,img
        
    def erode(self,seg,img,morph):
        key='ERODERAD'
        rad=self.getValue(seg,morph,key)
        if rad is None or rad<=0:
            return seg,img
    
    
        dim=np.int(2*rad+1)
        kern=np.ones((dim,dim),dtype=np.int)
    
        eroded=sn.binary_erode(seg.data == self.segid,
                               structure=kern).astype(np.int)
    
        b=np.where((seg.data != 0) & (seg.data!=self.segid))
        g=np.where(eroded)
        eroded[g]=seg.data[g]
        eroded[b]=seg.data[b]
    
        seg.data=eroded
        seg[key]=rad
        return seg,img

    def isophotal(self,seg,img,morph):
        key='SBLIM'
        sblim=self.getValue(seg,morph,key)
        if sblim is None:
            return seg,img

        # will need the zweropoint

    def maxsize(self,seg,img,morph):
        key='MAXRAD'
        maxrad=self.getValue(seg,morph,key)
        if maxrad is None or maxrad <= 0:
            return seg,img
    

    def rebin(self,seg,img,morph):
        #print('appears to use numpy.reshape and mean.  not sure yet')
        # in IDL, i used any pixel that contains info

        key='BINFACT'
        binfact=self.getValue(seg,morph,key)
        if binfact is None or binfact <=0:
            return seg,img
        
        binfact=int(binfact)

