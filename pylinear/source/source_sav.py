import numpy as np
import scipy.ndimage as sn

from ..sedphot import SED
from ..wcs import WCS
from ..utilities import convexhull
from . import morpho
from .extractionparameters import ExtractionParameters



class Source(WCS,ExtractionParameters):
    SEGTYPE=np.uint32      # for all segIDs to have this type
    
    def __init__(self,img,seg,zero,verbose=True,boolean=False,segid=None,
                 filtsig=None,eroderad=None,binfact=None,
                 minpix=0,maglim=None):


        
        # assume the best in our sources (ie that it is valid)
        self.valid=True
        
        # get the SEGID
        if segid is None:
            if 'SEGID' in seg.header:
                segid=seg.header['SEGID']
            else:
                print('[warn]Segmentation ID is missing from the header.')
                self.valid=False
                return
        self.segid=self.SEGTYPE(segid)

        # check that img/seg headers match
        #keys=['NAXIS','NAXIS2','CRPIX1','CRPIX2','CRVAL1','CRVAL2', \
        #      'CD1_1','CD1_2','CD2_1','CD2_2','CTYPE1','CTYPE2']
        #for key in keys:
        #    if key not in img.header:
        #        print('[warn]{} missing from image: {}'.format(key,self.segid))
        #        self.valid=False
        #    if key not in seg.header:
        #        print('[warn]{} missing from segmap: {}'.format(key,self.segid))
        #        self.valid=False
        #    if img.header[key]!=seg.header[key]:
        #        print('[warn]Incompatible headers: {}'.format(self.segid))
        #        self.valid=False
        #if not self.valid:
        #    return

        # apply morphological operators.  I'm coding it this way because
        # one day it might be useful to expose the order of these operators
        # since they definitely do not commute
        morphs=[(morpho.smooth,(filtsig,)),
                (morpho.erode,(eroderad,)),
                (morpho.rebin,(binfact,))]
        for func,val in morphs:
            seg,img=func(seg,img,self.segid,*val)
        

        # get the good pixels
        val=1 if boolean else self.segid    # the value to test against
        g=np.where(seg==val)                # the pixels to model
        npix=len(g[0])                      # number of good pixels

        # check that the source has enough valid pixels
        if npix<=minpix:
            print('[warn]Too few pixels for {}'.format(self.segid))
            self.valid=False
            return

        # initialize an SED object
        #self.sed=SED()

        # initialize the WCS
        WCS.__init__(self,seg.header)

        # initialize the extraction wavelengths
        ExtractionParameters.__init__(self,
                                      lamb0=seg.get('LAMB0',None),
                                      lamb1=seg.get('LAMB1',None),
                                      dlamb=seg.get('DLAMB',None))

        # set the pixels associated.  Recall that Python is invert :'(
        self.xd=g[1]         # direct image x-coordinate
        self.yd=g[0]         # direct image y-coordinate

        # compute the area of the sources
        self.area=npix*self.pixelarea

                
        # compute brightnesses
        self.total=np.sum(img[g])

        # check the flux
        if self.total>0:
            self.mag=-2.5*np.log10(self.total)+zero
            
            # check the mag limit
            if maglim is not None and self.mag > maglim:
                print('[warn]below the mag limit for {}'.format(self.segid))
                self.valid=False

            # record the pixel weights
            self.wht=img[g]/self.total

            # save the centroids
            self.xyc=np.array([np.average(self.xd,weights=self.wht),
                               np.average(self.yd,weights=self.wht)])
            self.adc=np.array(self.xy2ad(self.xyc[0],self.xyc[1]))
            
        elif self.total==0:
            print('[warn]zero flux for {}'.format(self.segid))
            self.valid=False
        else:
            print('[warn]negative flux for {}'.format(self.segid))
            self.valid=False
        if not self.valid:
            return False
        
        # record the pixels
        self.xyd=[(x-self.ltv[0],y-self.ltv[1]) for x,y,v in self]

    def pixelate(self):
        ''' turn the pixels into single sources '''
        pass

        

    def write_h5(self,h5):
        
        dtype=[('x',np.uint16),('y',np.uint16),('w',np.float64)]
        data=np.array(list(zip(self.xd,self.yd,self.wht)),dtype=dtype)
        hd=h5.create_dataset(str(self.segid),data=data)
        hd.attrs['total']=np.float32(self.total)
        hd.attrs['mag']=np.float32(self.mag)
        hd.attrs['area']=np.float32(self.area)
        hd.attrs['lamb0']=np.float32(self.lamb0)
        hd.attrs['lamb1']=np.float32(self.lamb1)
        hd.attrs['dlamb']=np.float32(self.dlamb)        
        hd.attrs['ltv']=np.int32(self.ltv)
        hd.attrs['xyc']=np.float32(self.xyc-self.ltv)
        hd.attrs['adc']=np.float64(self.adc)
        

    def instrumental_flux(self,img):
        xd=self.xd-int(self.ltv[0])
        yd=self.yd-int(self.ltv[1])
        tot=np.sum(img[yd,xd])
        return tot

    def set_SED(self,lamb,flam):
        self.sed=SED(lamb,flam)
        #self.sed.write('{}.sed'.format(self.segid))
        
    def load_SED(self,filename,bandpass):
        # load the SED 
        self.sed=SED.load(filename)
        
        # get the expected flux
        obsflam=self.total*bandpass.photflam
        
        # compute the average flux through the filter
        modflam=bandpass.aveflux(self.sed,flam=True)

        # scale SED so bandpass-averaged flux equals measured brightness
        self.sed*=(obsflam/modflam)


        #self.sed.write('{}.sed'.format(self.segid))

        

    def convex_hull(self):
        xh,yh=convexhull.vertices(self.xd,self.yd)
        return xh,yh
        
    @property
    def name(self):
        return '{}'.format(self.segid)

    def __str__(self):
        return 'Source segid={}'.format(self.segid)

    def __iter__(self):
        yield from zip(self.xd,self.yd,self.wht)

    def __len__(self):
        return len(self.xd)


    #@property
    #def pixels(self):
    #     pixels=[(x-self.ltv[0],y-self.ltv[1]) for x,y in zip(self.xd,self.yd)]
    #    return pixels

    
    #def pixels(self):    
    #    yield from ((x-self.ltv[0],y-self.ltv[1]) for x,y in zip(self.xd,self.yd))
