import numpy as np
import scipy.ndimage as sn
#from astropy.wcs import WCS

import pdb


from .direct import Direct
from .extractionparameters import ExtractionParameters

from pylinear.synthphot import SED
from pylinear.astro import WCS
from pylinear.utilities import convexhull



class Source(WCS,ExtractionParameters,Direct):
    SEGTYPE=np.uint32           # force SEGIDs to have this type

    def __init__(self,img,seg,zero,segid=None,minpix=3,maglim=26,            
                 lamb0=None,lamb1=None,dlamb=None,
                 filtsig=None,eroderad=None,binfact=None):

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
        operations=[(self.smooth,filtsig),
                    (self.erode,eroderad),
                    (self.rebin,binfact)]
        for func,val in operations:
            seg,img=func(seg,img,val)

        
        # get the good pixels
        g=np.where(seg == self.segid)
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
        self.zero=zero
        #self.total=np.sum(img.data[g])
        self.total=np.sum(img[g])
        if self.total>0:
            self.mag=-2.5*np.log10(self.total)+self.zero
            if self.mag >maglim:
                #print('[warn]Below mag limit for {}'.format(self.segid))
                self.valid=False
                return
            
            self.wht=img[g]/self.total

            # compute the centroids (in pixel and RA,Dec)
            self.xyc=np.array([np.average(self.xd,weights=self.wht), \
                               np.average(self.yd,weights=self.wht)])
            #self.adc=self.all_pix2world(*self.xyc,0)
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
    

    #def getValue(self,seg,morph,key):
    #    if key in seg:            # first check if it's present in the SEG
    #        return seg[key]
    #    if key in morph:          # second check if it's supplied by input
    #        return morph[key]
    #    return None               # default to None
    
    def smooth(self,seg,img,filtsig,key='FILTSIG'):
        
        if filtsig is None or filtsig <=0:
            return seg,img
        
        bad=seg.data != self.segid
        good=seg.data == self.segid
        V=img.data.copy()
        V[bad]=0
        VV=sn.gaussian_filter(V,sigma=filtsig)

        W=np.ones_like(img.data)
        W[bad]=0
        WW=sn.gaussian_filter(W,sigma=filtsig)
        Z=VV/WW
        img.data[good]=Z[good]

        seg[key]=filtsig
        
        return seg,img
        
    def erode(self,seg,img,eroderad,key='ERODERAD'):
        
        if eroderad is None or eroderad<=0:
            return seg,img
    
        dim=np.int(2*eroderad+1)
        kern=np.ones((dim,dim),dtype=np.int)

        good=seg == self.segid

        flux0=np.sum(img[np.where(good)])

        eroded=sn.binary_erosion(good,structure=kern).astype(np.int)
        
        b=np.where((seg != 0) & (seg != self.segid))
        g=np.where(eroded)
        eroded[g]=seg[g]
        eroded[b]=seg[b]

        flux1=np.sum(img[g])
        frat=flux0/flux1
        #print('scale the weights by this amount? or apply it post facto?')
        
        seg.image=eroded
        seg[key]=eroderad

        return seg,img

    def isophotal(self,seg,img,sblim):
        key='SBLIM'
        if sblim is None:
            return seg,img

        # will need the zweropoint (now in the self)

    def maxsize(self,seg,img,maxrad):
        key='MAXRAD'
        if maxrad is None or maxrad <= 0:
            return seg,img
    

    def rebin(self,seg,img,binfact,function='mean',key='BINFACT'):
        #print('appears to use numpy.reshape and mean.  not sure yet')
        # in IDL, i used any pixel that contains info

        
        if binfact is None or binfact <=1:
            return seg,img
        



        binfact=int(binfact)
        

        print("this is all to change with  FITSImage")
        q=input()

        
        dim=img.shape
        new=[(dim[0]+1)//binfact,(dim[1]+1)//binfact]
        bins=np.arange(dim[0]*dim[1]).reshape(dim)+1
        ones=np.ones((binfact,binfact),dtype=np.int)
        bins=np.kron(bins,ones)[:dim[0],:dim[1]]
        b=np.unique(bins)

        flo=function.lower()
        if flo=='mean': func=sn.mean
        elif flo=='sum': func=sn.sum
        elif flo=='median': func=sn.median
        else: func=sn.mean
        ave=func(img.data,labels=bins,index=b).reshape(new)

        img.data=ave
        img.naxis[0]=img.header['NAXIS1']=new[0]
        img.naxis[1]=img.header['NAXIS2']=new[1]
        img.crpix[0]=img.header['CRPIX1']=(img.header['CRPIX1']+0.5)/binfact+0.5
        img.crpix[1]=img.header['CRPIX2']=(img.header['CRPIX2']+0.5)/binfact+0.5
        img.cd[0,0]=img.header['CD1_1']=img.header['CD1_1']*binfact
        img.cd[1,0]=img.header['CD2_1']=img.header['CD2_1']*binfact
        img.cd[0,1]=img.header['CD1_2']=img.header['CD1_2']*binfact
        img.cd[1,1]=img.header['CD2_2']=img.header['CD2_2']*binfact

        g=np.where((seg.data != self.segid))[0]
        mx=seg.data
        mx[g]=0
        mx=sn.maximum(mx,labels=bins,index=b).reshape(new)
        zz=sn.maximum(seg.data,labels=bins,index=b).reshape(new)
        g=np.where(mx==0)[0]
        mx[g]=zz[g]

        seg.data=mx
        seg.naxis[0]=seg.header['NAXIS1']=new[0]
        seg.naxis[1]=seg.header['NAXIS2']=new[1]
        seg.crpix[0]=seg.header['CRPIX1']=(seg.header['CRPIX1']+0.5)/binfact+0.5
        seg.crpix[1]=seg.header['CRPIX2']=(seg.header['CRPIX2']+0.5)/binfact+0.5
        seg.cd[0,0]=seg.header['CD1_1']=seg.header['CD1_1']*binfact
        seg.cd[1,0]=seg.header['CD2_1']=seg.header['CD2_1']*binfact
        seg.cd[0,1]=seg.header['CD1_2']=seg.header['CD1_2']*binfact
        seg.cd[1,1]=seg.header['CD2_2']=seg.header['CD2_2']*binfact


        return seg,img
        
