import numpy as np
import datetime
from astropy.io import fits
from astropy.wcs import WCS as astropyWCS





class WCS(astropyWCS):
    ''' A class to override the astropy.wcs.WCS to do many more things '''


    #__RADEG__=180/np.pi
    
    def __init__(self,hdr):
        astropyWCS.__init__(self,hdr)


        # check some things
        if np.isnan(self.wcs.equinox):
                self.wcs.equinox=2000.
                

        
        # for reasons, they do not include LTV* in WCS
        self.ltv=np.array([0,0])
        if 'LTV1' in hdr:
            self.ltv[0]=hdr['LTV1']
        if 'LTV2' in hdr:
            self.ltv[1]=hdr['LTV2']
        
            
    #def makeSIP(self,sip):
    #    out={}
    #    ii,jj=np.where(sip != 0)
    #    out={(i,j):sip[i,j] for (i,j) in zip(ii,jj)}
    #    print(out)
        
        

    def pixelArea(self,x,y,scale=1.):
        ''' compute the pixel area for the distortion '''
        
        dx=np.array(x)-(self.wcs.crpix[0]-1.)
        dy=np.array(y)-(self.wcs.crpix[1]-1.)
        if np.isscalar(x):
            n=1
        else:
            n=len(x)


        # compute derivatives for A
        ii,jj=np.where(self.sip.a != 0)
        dadx=np.ones_like(dx)
        dady=np.zeros_like(dx)
        for i,j,v in zip(ii,jj,self.sip.a[ii,jj]):
            if i!=0:
                dadx+=(v*i*dx**(i-1)*dy**j)
            if j!=0:
                dady+=(v*j*dx**i*dy**(j-1))
                
            
            

        #dxy=dx.reshape((n,1))**(i-1)*dy.reshape((n,1))**j
        #dadx=np.dot(dxy,self.sip.a[i,j]*i)+1
        #dxy=dx.reshape((n,1))**i*dy.reshape((n,1))**(j-1)
        #dady=np.dot(dxy,self.sip.a[i,j]*j)


        # compute derivatives for B
        
        ii,jj=np.where(self.sip.b != 0)
        dbdx=np.zeros_like(dx)
        dbdy=np.ones_like(dx)
        for i,j,v in zip(ii,jj,self.sip.b[ii,jj]):
            if i!=0:
                dbdx+=(v*i*dx**(i-1)*dy**j)
            if j!=0:
                dbdy+=(v*j*dx**i*dy**(j-1))

        #dxy=dx.reshape((n,1))**(i-1)*dy.reshape((n,1))**j
        #dbdx=np.dot(dxy,self.sip.b[i,j]*i)
        #dxy=dx.reshape((n,1))**i*dy.reshape((n,1))**(j-1)
        #dbdy=np.dot(dxy,self.sip.b[i,j]*j)+1

        jacobian = scale*np.abs(dadx * dbdy - dady * dbdx)
        if n==1:
            jacobian=jacobian[0]
        
        return jacobian
        


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
            hdr['NAXIS1']=(self.shape[0],'Number of pixels in x-axis')
            hdr['NAXIS2']=(self.shape[1],'Number of pixels in y-axis')
            
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
            hdr['CD1_1']=(self.wcs.cd[0,0],'partial of first axis coordinate w.r.t. x') 
            hdr['CD2_1']=(self.wcs.cd[1,0],'partial of second axis coordinate w.r.t. x')
            hdr['CD1_2']=(self.wcs.cd[0,1],'partial of first axis coordinate w.r.t. y')
            hdr['CD2_2']=(self.wcs.cd[1,1],'partial of second axis coordinate w.r.t. y')
            if hasattr(self,'ltv0'):
                hdr['LTV1']=(self.ltv0,'x-axis pixel reference')
            if hasattr(self,'ltv0'):
                hdr['LTV2']=(self.ltv1,'y-axis pixel reference')

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


    def getrot(self,silent=True):
        #cd=self.wcs.cd/self.__RADEG__
        cd=np.deg2rad(self.wcs.cd)


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
                if np.rad2deg(np.abs(rot1-rot2))<2: #*self.__RADEG__ < 2:
                    rot=(rot1+rot2)/2.
                elif np.rad2deg(np.abs(rot1-rot2-2*np.pi))<2:#*self.__RADEG__ < 2:
                    rot=(rot1+rot2-2*np.pi)/2
                elif np.rad2deg(np.abs(rot1-rot2+2*np.pi))<2:#*self.__RADEG__ < 2:
                    rot=(rot1+rot2+2*np.pi)/2
                else:
                    if not silent:
                        print("WARNING: x/y axis rotations differ by >=2 deg")
                    rot=rot1
            else:
                rot=rot1
                    
                    
            
            pix=np.array([sgn*np.sqrt(cd[0,0]*cd[0,0]+cd[0,1]*cd[0,1]),\
                          np.sqrt(cd[1,1]*cd[1,1]+cd[1,0]*cd[1,0])])
            
            #rot=rot*self.__RADEG__
            rot=np.rad2deg(rot)
            
            if self.wcs.lonpole != 180:
                rot=rot+(180-self.wcs.lonpole)
            
        #pix=pix*self.__RADEG__
        pix=np.rad2deg(pix)
        return rot,pix

    @property
    def pixelscale(self):
        rot,cdelt=self.getrot()
        return abs(cdelt)*3600
    
    @property
    def pixelarea(self):
        rot,cdelt=self.getrot()
        area=-(cdelt[0]*3600)*(cdelt[1]*3600)
        return area

    #def formatter(func):
    #    def wrapper(*args,**kwargs):
    #        a,b=func(*args,**kwargs)
    #        #if a.size==1:
    #        #    print(a)
    #        #    a=a[0]
    #        #    b=b[0]
    #        return a,b
    #    return wrapper

    

    # convenience functions because that zero is poor design
    #@formatter
    def xy2ad(self,x,y):
        return self.all_pix2world(x,y,0)

    def ad2xy(self,a,d):
        return self.all_world2pix(a,d,0)

    def xy2xy(self,x,y,obj):
        a,d=self.all_pix2world(x,y,0)
        return obj.all_world2pix(a,d,0)
    
    
        
if __name__=='__main__':
    with fits.open('/Users/rryan/icoi3immq_flt.fits') as hdul:
        hdr=hdul[1].header
    x=WCS(hdr)
    
    a,d=x.xy2ad(np.array([10]),np.array([20]))
    print(a[0])
