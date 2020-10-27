import numpy as np
import datetime
from astropy.io import fits
from astropy.wcs import WCS as astropyWCS
import astropy.wcs.utils as wcsutils
import re


def formatter(func):
    def wrapper(*args,**kwargs):
        a,b=func(*args,**kwargs)
        if isinstance(a,np.ndarray) and a.ndim==0:
            a=a.item()
            b=b.item()
        return a,b
    return wrapper



class WCS(astropyWCS):
    ''' A class to override the astropy.wcs.WCS to do many more things '''

    
    def __init__(self,hdr):
        # ok, there is this annoying situation where the SIP coefs will
        # be present, but the CTYPE does not indicate that.  Therefore,
        # astropy will issue a big warning, so I'll take control of that
        # here, but checking for SIP coefs and the CTYPE
        #has_sip=self.has_sip(hdr)
        #if has_sip:
        #    for ctype in ('CTYPE1','CTYPE2'):
        #        if hdr[ctype][8:] != '-SIP':
        #            hdr[ctype] += '-SIP'



        # set the astropy WCS class
        astropyWCS.__init__(self,header=hdr)


        self.shape=(hdr['NAXIS2'],hdr['NAXIS1'])
        self.npixel=self.shape[0]*self.shape[1]

        
        # check some things
        if np.isnan(self.wcs.equinox):
                self.wcs.equinox=2000.
                        
        # for reasons, they do not include LTV* in WCS
        self.ltv=np.array([0,0])
        if 'LTV1' in hdr:
            self.ltv[0]=hdr['LTV1']
        if 'LTV2' in hdr:
            self.ltv[1]=hdr['LTV2']


            
   
    def pixel_area_map(self,x,y,scale=1.):
        ''' compute the pixel area for the distortion '''
        
        dx=np.array(x)-(self.wcs.crpix[0]-1.)
        dy=np.array(y)-(self.wcs.crpix[1]-1.)
        if np.isscalar(x):
            n=0
        else:
            n=len(x)


        # compute derivatives for A
        dadx=np.ones_like(dx)
        dady=np.zeros_like(dx)
        if hasattr(self.sip,'a'):
            ii,jj=np.where(self.sip.a != 0)
            for i,j,v in zip(ii,jj,self.sip.a[ii,jj]):
                if i!=0:
                    dadx+=(v*i*dx**(i-1)*dy**j)
                if j!=0:
                    dady+=(v*j*dx**i*dy**(j-1))
                
            
            

        # compute derivatives for B         
        dbdx=np.zeros_like(dx)
        dbdy=np.ones_like(dx)
        if hasattr(self.sip,'b'):
            ii,jj=np.where(self.sip.b != 0)
            for i,j,v in zip(ii,jj,self.sip.b[ii,jj]):
                if i!=0:
                    dbdx+=(v*i*dx**(i-1)*dy**j)
                if j!=0:
                    dbdy+=(v*j*dx**i*dy**(j-1))

        jacobian = scale*np.abs(dadx * dbdy - dady * dbdx)
        
        if n==1:
            jacobian=jacobian[0]
        
        return jacobian



    def has_sip(self,hdr):

        keys=list(hdr.keys())        
        for func in ('A','B','AP','BP'):
            # build a regex search
            r = re.compile("{}_[0-9]_[0-9]".format(func))

            
            # has a given order
            if '{}_ORDER'.format(func) in keys and any(filter(r.match,keys)):
                return True
        return False
            

            
    def putSIP(self,hdr,sip,name):
        if sip is not None:
            ii,jj=np.where(sip !=0)
            order=getattr(self.sip,'{}_order'.format(name.lower()))
            hdr['{}_ORDER'.format(name)]=order
            for (i,j,v) in zip(ii,jj,sip[ii,jj]):
                hdr['{}_{}_{}'.format(name,i,j)]=v
        
    def mkhdr(self,dtype,**kwargs):       

        if self.wcs.ctype[0][0:8]=='RA---TAN' and \
           self.wcs.ctype[1][0:8]=='DEC--TAN':

            hdr=fits.Header()
            hdr['SIMPLE']=(True,'Created by pyLINEAR (R. Ryan)')
            if dtype == np.float64:
                bitpix=-64
            elif dtype == np.float32:
                bitpix=-32
            elif dtype == np.int16:
                bitpix=16
            elif dtype == np.int32:
                bitpix=32
            elif dtype == np.int64:
                bitpix=64
            else:
                raise NotImplementedError("NumPy type of {} is unknown.".format(dtype))
            hdr['BITPIX']=(bitpix,'Number of bits per data pixel')

            
            now=datetime.datetime.now().strftime("%Y-%m-%d")
            hdr['DATE']=(now,'Creation UTC (CCCC-MM-DD) date of FITS header')
            hdr['NAXIS']=(2,'Number of data axes')
            hdr['NAXIS1']=(self.shape[1],'Number of pixels in x-axis')
            hdr['NAXIS2']=(self.shape[0],'Number of pixels in y-axis')
            
            # put in the astrometry
            hdr['CRPIX1']=(self.wcs.crpix[0],'x-coordinate of reference pixel')
            hdr['CRPIX2']=(self.wcs.crpix[1],'y-coordinate of reference pixel')
            hdr['CRVAL1']=(self.wcs.crval[0],'first axis value at reference pixel')
            hdr['CRVAL2']=(self.wcs.crval[1],'second axis value at reference pixel')

            # astropy complains about this.  Stupid astropy 
            #hdr['CDELT1']=(self.wcs.cdelt[0],' ')
            #hdr['CDELT2']=(self.wcs.cdelt[1],' ')

            hdr['CTYPE1']=(self.wcs.ctype[0],'the coordinate type for the first axis') 
            hdr['CTYPE2']=(self.wcs.ctype[1],'the coordinate type for the second axis')

            cd=self.cd(unit='deg')
            hdr['CD1_1']=(cd[0,0],'partial of first axis coordinate w.r.t. x') 
            hdr['CD2_1']=(cd[1,0],'partial of second axis coordinate w.r.t. x')
            hdr['CD1_2']=(cd[0,1],'partial of first axis coordinate w.r.t. y')
            hdr['CD2_2']=(cd[1,1],'partial of second axis coordinate w.r.t. y')


            if hasattr(self,'ltv'):
                hdr['LTV1']=(self.ltv[0],'x-axis pixel reference')
                hdr['LTV2']=(self.ltv[1],'y-axis pixel reference')

            if np.isnan(self.wcs.equinox):
                hdr['EQUINOX']=(2000.,'Equinox of Ref. Coord.')
            else:
                hdr['EQUINOX']=(self.wcs.equinox,'Equinox of Ref. Coord.')
            hdr['LONGPOLE']=(self.wcs.lonpole,' ')

            
            if self.wcs.ctype[0][9:]==self.wcs.ctype[1][9:]=='SIP':
                self.putSIP(hdr,self.sip.a,'A')
                self.putSIP(hdr,self.sip.b,'B')
                self.putSIP(hdr,self.sip.ap,'AP')
                self.putSIP(hdr,self.sip.bp,'BP')


            # add any additional keywords
            for k,v in kwargs.items():
                hdr[k]=v
       


        else:
            raise NotImplementedError("Invalid CTYPE")

        return hdr


    def cd(self,unit='deg'):

        try:
            cd=self.wcs.cd
        except:
            #if ~self.wcs.has_cd():
            cd=self.pixel_scale_matrix
            cd[0,:]*=self.wcs.cdelt[0]
            cd[1,:]*=self.wcs.cdelt[1]            

 

        if unit=='rad':
            cd=np.deg2rad(cd)
        elif unit=='arcsec':
            cd*=3600.
        elif unit=='arcmin':
            cd*=60.
        elif unit=='deg':
            pass            
        else:
            raise NotImplementedError('invalud unit: {}'.format(unit))

        return cd
        

    
    def getrot(self,silent=True):

        cd=self.cd(unit='rad')

        # astropy throws this as a warning
        #if self.wcs.cdelt[0] != 1:
        #    cd[0,:]=cd[0,:]*self.wcs.cdelt[0]
        #if self.wcs.cdelt[1] != 1:
        #    cd[1,:]=cd[1,:]*self.wcs.cdelt[1]
        

            
        det=cd[0,0]*cd[1,1]-cd[0,1]*cd[1,0]
        if det < 0:
            sgn=-1
        else:
            sgn=+1

        if (cd[1,0] == 0) and (cd[0,1]==0):
            rot=0.
            pix=np.array([cd[0,0],cd[1,1]])
        else:
            rot1=np.arctan2(sgn*cd[0,1],sgn*cd[0,0])
            rot2=np.arctan2(-cd[1,0],cd[1,1])

            
            if rot1 != rot2:
                if np.rad2deg(np.abs(rot1-rot2))<2:
                    rot=(rot1+rot2)/2.
                elif np.rad2deg(np.abs(rot1-rot2-2*np.pi))<2:
                    rot=(rot1+rot2-2*np.pi)/2
                elif np.rad2deg(np.abs(rot1-rot2+2*np.pi))<2:
                    rot=(rot1+rot2+2*np.pi)/2
                else:
                    if not silent:
                        print("WARNING: x/y axis rotations differ by >=2 deg")
                    rot=rot1
            else:
                rot=rot1
                    
                    
            
            pix=np.array([sgn*np.sqrt(cd[0,0]*cd[0,0]+cd[0,1]*cd[0,1]),\
                          np.sqrt(cd[1,1]*cd[1,1]+cd[1,0]*cd[1,0])])
            
            rot=np.rad2deg(rot)
            
            if self.wcs.lonpole != 180:
                rot=rot+(180-self.wcs.lonpole)

        print('here')
        pix=np.rad2deg(pix)
        return rot,pix

    @property
    def pixelscale(self):
        #rot,cdelt=self.getrot()
        #scales=np.abs(cdelt)
        scales=wcsutils.proj_plane_pixel_scales(self)        
        return scales*3600.

        
        
    @property
    def pixelarea(self):
        #rot,cdelt=self.getrot()
        #area=-(cdelt[0]*3600)*(cdelt[1]*3600)
        pscl=self.pixelscale
        area=pscl[0]*pscl[1]        
        return area


    # convenience functions because that zero is poor design
    @formatter
    def xy2ad(self,x,y):
        return self.all_pix2world(x,y,0)

    @formatter
    def ad2xy(self,a,d):
        return self.all_world2pix(a,d,0)

    @formatter
    def xy2xy(self,x,y,obj):
        assert isinstance(obj,astropyWCS)
        a,d=self.all_pix2world(x,y,0)
        return obj.all_world2pix(a,d,0)
        #xx,yy=obj.all_world2pix(a,d,0)
        #return xx+0.5,yy+0.5
        
        
    
        
if __name__=='__main__':
    with fits.open('/Users/rryan/MACS0647/data1/pre_Z11_-25_1.302_G141/icc905meq_flt.fits') as hdul:
        hdr=hdul[1].header
    wcs=WCS(hdr)


    import fitsimage
    x=fitsimage.FITSImage('/Users/rryan/MACS0647/data/CLASH/65mas/z11_seg.fits')

    y=x.extract(50,70,50,70)
    print(y)

    a,d=y.xy2ad(10,10)
    print(a,d)
    xx,yy=wcs.ad2xy(a,d)
    print(xx,yy)
    
    #a,d=wcs.xy2ad(np.array([11]),np.array([21]))
    
    #print(a,d)
    #x,y=wcs.ad2xy(a,d)

    #print(x,y)
    #x,y=wcs.xy2xy(11,21,wcs)
    #print(x,y)

