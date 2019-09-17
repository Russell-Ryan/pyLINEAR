import numpy as np
import re
import os
import datetime
from astropy.io import fits

class WCS(object):
    __RADEG__=180/np.pi
    __NORTH__=1e-7*__RADEG__     # Called north_offset in wcssph2xy
    __SOUTH__=1e-7*__RADEG__     # Called south_offset in wcssph2xy
    
    def __init__(self,hdr,name=None):

        self.WCSname=name
        self.naxis=np.zeros(2,dtype=int)
        self.cd=np.zeros((2,2))
        self.crpix=np.zeros(2)
        self.crval=np.zeros(2)
        self.cdelt=np.ones(2)     # default to unity
        self.ctype=['','']
        self.ltv=np.zeros(2)
        self.equinox=2000.0       # always assume this is J2000
        self.longpole=180.        # always assume this is 180d
        self.a_order,self.b_order=0,0
        self.ap_order,self.bp_order=0,0
        self.a={}
        self.b={}
        self.ap={}
        self.bp={}

        self.loadHDR(hdr)

        

    def pixelArea(self,x,y,scale=1.):
        # renormalize w.r.t. the CRPIX
        dx=np.array(x)-(self.crpix[0]-1.)
        dy=np.array(y)-(self.crpix[1]-1.)
        
        # compute derivatives for A
        dadx=np.ones_like(dx)
        dady=np.zeros_like(dx)       
        for (i,j),val in self.a.items():
            if i >= 1:
                dadx+=(val*i*dx**(i-1)*dy**j)
            if j >= 1:
                dady+=(val*j*dx**i*dy**(j-1))

        # compute derivatives for B
        dbdx=np.zeros_like(dx)
        dbdy=np.ones_like(dx)
        for (i,j),val in self.b.items():
            if i >= 1:
                dbdx+=(val*i*dx**(i-1)*dy**j)
            if j >= 1:
                dbdy+=(val*j*dx**i*dy**(j-1))

        # compute rescaled Jacobian
        jacobian = scale*np.abs(dadx * dbdy - dady * dbdx)
        
        return jacobian
        

        
    def astrometry(self):
        print(self.WCSname)
        print("NAXIS {} {}".format(*self.naxis))
        print("CRPIX {} {}".format(*self.crpix))
        print("CRVAL {} {}".format(*self.crval))
        print("CD    {} {}\n      {} {}".format(self.cd[0,0],self.cd[1,0],\
                                                self.cd[0,1],self.cd[1,1]))

    def mkhdr(self,dtype,**kwargs):
        def putsip(hdr,dic,root):
            order=root.lower()+'_order'
            if hasattr(self,order):
                hdr[root.upper()+'_ORDER']=(getattr(self,order),' ')
                for k,v in dic.items():
                    key=root+'_{}_{}'.format(*k)
                    hdr[key]=(v,' ')

        # create the header
        hdr=fits.Header()
        hdr['SIMPLE']=(True,'Created by Python module WCS (R. Ryan for LINEAR)')
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
        hdr['NAXIS1']=(self.naxis[0],'Number of pixels in x-axis')
        hdr['NAXIS2']=(self.naxis[1],'Number of pixels in y-axis')

        # put in the astrometry
        hdr['CRPIX1']=(self.crpix[0],'x-coordinate of reference pixel')
        hdr['CRPIX2']=(self.crpix[1],'y-coordinate of reference pixel')
        hdr['CRVAL1']=(self.crval[0],'first axis value at reference pixel')
        hdr['CRVAL2']=(self.crval[1],'second axis value at reference pixel')
        hdr['CDELT1']=(self.cdelt[0],' ')
        hdr['CDELT2']=(self.cdelt[1],' ')
        hdr['CTYPE1']=(self.ctype[0],'the coordinate type for the first axis') 
        hdr['CTYPE2']=(self.ctype[1],'the coordinate type for the second axis')
        hdr['CD1_1']=(self.cd[0,0],'partial of first axis coordinate w.r.t. x') 
        hdr['CD2_1']=(self.cd[1,0],'partial of second axis coordinate w.r.t. x')
        hdr['CD1_2']=(self.cd[0,1],'partial of first axis coordinate w.r.t. y')
        hdr['CD2_2']=(self.cd[1,1],'partial of second axis coordinate w.r.t. y')
        hdr['LTV1']=(self.ltv[0],'x-axis pixel reference')
        hdr['LTV2']=(self.ltv[1],'x-axis pixel reference')
        
        hdr['EQUINOX']=(self.equinox,'Equinox of Ref. Coord.')
        hdr['LONGPOLE']=(self.longpole,' ')
        
        # add the sip to the header
        putsip(hdr,self.a,'a')
        putsip(hdr,self.b,'b')
        putsip(hdr,self.ap,'ap')
        putsip(hdr,self.bp,'bp')
        
        
        # add any additional keywords
        for k,v in kwargs.items():
            hdr[k]=v

        return hdr


    def _checkDefault(self,key,hdr,default):
        if (key in hdr):
            if (hdr[key] != default):
                raise NotImplementedError("{} must be set to default.".format(key))
        
    def loadHDR(self,hdr):


        self._checkDefault('EQUINOX',hdr,self.equinox)
        self._checkDefault('LONGPOLE',hdr,self.longpole)

        
        self.naxis[0]=hdr['NAXIS1']
        self.naxis[1]=hdr['NAXIS2']
        self.cd[0,0]=hdr['CD1_1']
        self.cd[0,1]=hdr['CD1_2']
        self.cd[1,0]=hdr['CD2_1']
        self.cd[1,1]=hdr['CD2_2']
        self.crpix[0]=hdr['CRPIX1']
        self.crpix[1]=hdr['CRPIX2']
        self.crval[0]=hdr['CRVAL1']
        self.crval[1]=hdr['CRVAL2']
        if 'CDELT1' in hdr:
            self.cdelt[0]=hdr['CDELT1']
        if 'CDELT2' in hdr:
            self.cdelt[1]=hdr['CDELT2']
        self.ctype[0]=hdr['CTYPE1']
        self.ctype[1]=hdr['CTYPE2']


        if 'LTV1' in hdr:
            self.ltv[0]=hdr['LTV1']
        if 'LTV2' in hdr:
            self.ltv[1]=hdr['LTV2']
            
        if (self.ctype[0][0:8] != 'RA---TAN') or \
           (self.ctype[1][0:8] != 'DEC--TAN'):
            raise NotImplementedError("only RA/Dec-TAN projections")
        if (self.ctype[0][9:12] == 'SIP') and (self.ctype[1][9:12] == 'SIP'):
            regex=re.compile('(A|B|AP|BP)_[0-9]+_[0-9]+')
            
            if 'A_ORDER' in hdr:
                self.a_order=hdr['A_ORDER']
            if 'B_ORDER' in hdr:
                self.b_order=hdr['B_ORDER']
            if 'AP_ORDER' in hdr:
                self.ap_order=hdr['AP_ORDER']
            if 'BP_ORDER' in hdr:
                self.bp_order=hdr['BP_ORDER']

                
            for k,v in hdr.items():
                if regex.match(k):
                    spl=k.split('_')
                    key=(int(spl[1]),int(spl[2]))
                    
                    if spl[0]=='A':
                        self.a[key]=v
                    elif spl[0]=='B':
                        self.b[key]=v
                    elif spl[0]=='AP':
                        self.ap[key]=v
                    elif spl[0]=='BP':
                        self.bp[key]=v
                    else:
                        print("Invalid SIP function: {} {} {}".format(*spl))

    def getrot(self,silent=True):
        cd=self.cd/self.__RADEG__

        cd[0,:]=cd[0,:]*self.cdelt[0]
        cd[1,:]=cd[1,:]*self.cdelt[1]

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
                if np.abs(rot1-rot2)*self.__RADEG__ < 2:
                    rot=(rot1+rot2)/2.
                elif np.abs(rot1-rot2-2*np.pi)*self.__RADEG__ < 2:
                    rot=(rot1+rot2-2*np.pi)/2
                elif np.abs(rot1-rot2+2*np.pi)*self.__RADEG__ < 2:
                    rot=(rot1+rot2+2*np.pi)/2
                else:
                    if not silent:
                        print("WARNING: x/y axis rotations differ by >=2 deg")
                    rot=rot1
            else:
                rot=rot1
                    
                    
            
            pix=np.array([sgn*np.sqrt(cd[0,0]*cd[0,0]+cd[0,1]*cd[0,1]),\
                          np.sqrt(cd[1,1]*cd[1,1]+cd[1,0]*cd[1,0])])
            
            rot=rot*self.__RADEG__
            if self.longpole != 180:
                rot=rot+(180-self.longpole)
            
        pix=pix*self.__RADEG__

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
        
    def sip(self,a,b,dx,dy):
        # apply SIP
        delx=dx        
        for key,val in a.items():
            delx=delx+val*dx**key[0]*dy**key[1]
            
        dely=dy
        for key,val in b.items():
            dely=dely+val*dx**key[0]*dy**key[1]

        return delx,dely

    def xy2xy(self,x1,y1,obj):
        aa,dd=self.xy2ad(x1,y1)
        x2,y2=obj.ad2xy(aa,dd)
        return x2,y2

    
    def xy2ad(self,x,y):
        #if np.isscalar(x): x=np.array(x)
        #if np.isscalar(y): y=np.array(y)
        #assert (x.shape==y.shape)

        
        #compute differentials
        delx=x-(self.crpix[0]-1)
        dely=y-(self.crpix[1]-1)
        
        
        #apply SIP if present
        if bool(self.a) and bool(self.b):
            dx,dy=self.sip(self.a,self.b,delx,dely)
        else:
            dx,dy=delx,dely


            
        # put this in an init method
        cd=self.cd
        cd[0,:]=cd[0,:]*self.cdelt[0]
        cd[1,:]=cd[1,:]*self.cdelt[1]
        ################
        
        #transform
        xsi=(cd[0,0]*dx+cd[0,1]*dy)
        eta=(cd[1,0]*dx+cd[1,1]*dy)
        
        # project on to sphere
        a,d=self.__xy2sph__(xsi,eta)
        return a,d

    def ad2xy(self,a,d,**kwargs):
        xsi,eta=self.__sph2xy__(a,d)
        
        # could put this in an init method
        cd=self.cd.copy()
        cd[0,:]=cd[0,:]*self.cdelt[0]
        cd[1,:]=cd[1,:]*self.cdelt[1]

        ####### COMPUTE INVERSE OF CD MATRIX ########
        scl=1e-5    # take this out to avoid rounding errors
        cd/=scl
        det=(cd[0,0]*cd[1,1]-cd[0,1]*cd[1,0])*scl
        if np.isinf(det):
            raise RuntimeError("Infinite Determinant in CD matrix")
        
        fac=scl/det
        cdinv=np.zeros_like(cd)
        cdinv[0,0]=cd[1,1]/det
        cdinv[1,1]=cd[0,0]/det
        cdinv[0,1]=-cd[0,1]/det
        cdinv[1,0]=-cd[1,0]/det
                    

        #cdinv=np.linalg.inv(cd)
        #############################################
        
        xdif=cdinv[0,0]*xsi+cdinv[0,1]*eta
        ydif=cdinv[1,0]*xsi+cdinv[1,1]*eta
        
        
        if bool(self.ap) and bool(self.bp):
            # if have inverse SIP, just use them!
            dx,dy=self.sip(self.ap,self.bp,xdif,ydif)

            x=dx+(self.crpix[0]-1)
            y=dy+(self.crpix[1]-1)
        else:
            if bool(self.a) and bool(self.b):
                # no inverse SIP, but have forward SIP.  So INVERT!!!!
                xu=xdif+(self.crpix[0]-1)
                yu=ydif+(self.crpix[1]-1)
                x,y=self.invert_sip(xu,yu,**kwargs)
            else:
                # no SIP present.  so just apply the CRPIX
                x=xdif+(self.crpix[0]-1)
                y=ydif+(self.crpix[1]-1)
        return x,y

    def invert_sip(self,xu,yu,tolerance=1e-3,maxiterations=100):
        # see new_ad2xy.pro in the Experimental directory --- based on
        # Andrea Bellini's description of Jay Anderson's implementation
        iteration=0
        tolerance2=tolerance*tolerance

        x,y=xu,yu
        done=False
        while not done:
            dx=x-(self.crpix[0]-1)
            dy=y-(self.crpix[1]-1)
            
            delx,dely=self.sip(self.a,self.b,dx,dy)

            dx=xu-(delx+(self.crpix[0]-1))
            dy=yu-(dely+(self.crpix[1]-1))
            
            x=x+dx/2.
            y=y+dy/2.

            dr2max=np.amax(dx*dx+dy*dy)
            iteration=iteration+1
            done=(dr2max <= tolerance2) or (iteration == maxiterations)
        return x,y
            
            
    

    def __rotate__(self,phi,theta,reverse):

        # could put this in an initialization method
        # assume TANGENT projections
        phi_p=np.pi
        sp=0.
        cp=-1.
        alpha_p=self.crval[0]/self.__RADEG__
        delta_p=self.crval[1]/self.__RADEG__
        sa=np.sin(alpha_p)
        ca=np.cos(alpha_p)
        sd=np.sin(delta_p)
        cd=np.cos(delta_p)
        rotmat=np.array([[-sa*sp-ca*cp*sd,ca*sp-sa*cp*sd,cp*cd ],\
                         [sa*cp-ca*sp*sd,-ca*cp-sa*sp*sd,sp*cd ] ,\
                         [ca*cd,sa*cd, sd]])
        ########################################

        if reverse:
            lat,lon=phi,theta
            phi1=phi/self.__RADEG__
            theta1=theta/self.__RADEG__
            rot=np.transpose(rotmat)
        else:
            phi1=phi/self.__RADEG__
            theta1=theta/self.__RADEG__
            rot=rotmat

        # compute some angles
        l=np.cos(theta1)*np.cos(phi1)
        m=np.cos(theta1)*np.sin(phi1)
        n=np.sin(theta1)
            
        # python indexing is backward of IDL
        b0=rot[0,0]*l+rot[0,1]*m+rot[0,2]*n
        b1=rot[1,0]*l+rot[1,1]*m+rot[1,2]*n
        b2=rot[2,0]*l+rot[2,1]*m+rot[2,2]*n

        # trim bad values
        b2=np.clip(b2,-1.,+1.)

        y=np.arcsin(b2)*self.__RADEG__
        x=np.arctan2(b1,b0)*self.__RADEG__

        return x,y

    def __xy2sph__(self,x,y):

        r=np.hypot(x,y)
        
        #theta=np.where(r>0,np.arctan(self.__RADEG__/r),np.full_like(x,np.pi/2))

        theta=np.full_like(r,np.pi/2.)
        g=np.where(r>0)[0]
        if len(g)!=0:
            theta[g]=np.arctan(self.__RADEG__/r[g])

        
        phi=np.arctan2(x,-y)

        
        phi=phi*self.__RADEG__
        theta=theta*self.__RADEG__

        lon,lat=self.__rotate__(phi,theta,True)

        lon=np.where(lon<0,lon+360,lon)
        lon=np.where(lon>=359.99,lon-360,lon)

        
        return lon,lat
        
    def __sph2xy__(self,lon0,lat0):
        lon=lon0
        lat=lat0

        # center around 0
        lon=np.where(lon>=180,lon-360,lon)
        
        # fix data near poles
        lat=np.where(np.abs(lat-90)<self.__NORTH__,90.-self.__NORTH__,lat)
        lat=np.where(np.abs(lat+90)<self.__SOUTH__,90.+self.__SOUTH__,lat)
        

        # apply rotation
        phi,theta=self.__rotate__(lon,lat,False)
        phi=phi/self.__RADEG__
        theta=theta/self.__RADEG__

        # set values
        x=np.full_like(lon,0.)
        y=np.full_like(lon,0.)

        r=self.__RADEG__/np.tan(theta)
        x= r*np.sin(phi)
        y=-r*np.cos(phi)
        
        return x,y


if __name__=='__main__':
    print('testing WCS class')

    hdr=fits.getheader(os.environ['LINEAR_CONFIG']+os.sep+'HST/WFC3/IR/hst_wfc3_ir_fov.fits','IR')

    
    q=WCS(hdr)
    q.cd[0,0]=+2.35007487532090E-05
    q.cd[0,1]=-2.6169687278019E-05
    q.cd[1,0]=-2.9378019274077E-05
    q.cd[1,1]=-2.1078301735985E-05
    q.crval[0]=189.1792282504428
    q.crval[1]=62.28646067642324 


    q.naxis[0]=1014
    q.naxis[1]=1014
    q.cd[0,0]=+2.35007487532090E-05
    q.cd[0,1]=-2.6169687278019E-05
    q.cd[1,0]=-2.9378019274077E-05
    q.cd[1,1]=-2.1078301735985E-05
    q.crpix[0]=507.
    q.crpix[1]=507.
    q.crval[0]=189.1792282504428
    q.crval[1]=62.28646067642324 
    q.ctype[0]='RA---TAN-SIP'
    q.ctype[1]='DEC--TAN-SIP'


    q.a[(0,2)]= 5.33092691853019E-08
    q.a[(0,3)]= 3.73753772880087E-11
    q.a[(0,4)]=-2.0211147283637E-13    
    q.a[(1,1)]= 2.44084308174762E-05
    q.a[(1,2)]= 2.81394789152228E-11
    q.a[(1,3)]= 5.17856894659408E-13
    q.a[(2,0)]=-2.4133465663211E-07
    q.a[(2,1)]= 1.29289254704036E-10  
    q.a[(2,2)]= 2.35753629384072E-14
    q.a[(3,1)]= 5.43714947358335E-13    
    q.a[(4,0)]=-2.8102976693048E-13

    q.b[(0,2)]= 2.99270373714981E-05
    q.b[(0,3)]=-2.3813607426051E-10
    q.b[(0,4)]= 7.23205168173609E-13
    q.b[(1,1)]=-1.7107385824843E-07
    q.b[(1,2)]= 6.31243430776636E-11
    q.b[(1,3)]=-5.1674434652779E-14
    q.b[(2,0)]= 6.95458963321812E-06
    q.b[(2,1)]=-3.0827896112996E-10
    q.b[(2,2)]=-1.7580091715687E-13    
    q.b[(3,0)]= 3.51974158902385E-11
    q.b[(3,1)]= 5.60993015610249E-14 
    q.b[(4,0)]=-5.9243852454034E-13



    #pamnorm=q.pixelArea(557.,557.)


    x,y=np.arange(1014),np.arange(1014)

    pam=np.zeros((1014,1014))
    for yy in y:
        yyy=np.zeros(1014)+yy
        p=q.pixelArea(x,yyy)
        pam[yy,:]=p

    pamnorm=pam[556,556]
        
    pam=pam/pamnorm


        
    hdulist=fits.HDUList()
    hdulist.append(fits.ImageHDU(data=pam))
    hdulist.writeto('test_pam.fits',overwrite=True)

    print('done')




    q=input()
    

    # dump to file
    hdulist=fits.HDUList()
    hdulist.append(fits.ImageHDU(data=np.zeros((1014,1014)),\
                                 header=q.mkhdr(np.int16)))
    hdulist.writeto('test_flt.fits',overwrite=True)




    
    a=np.array([189.1339431])
    d=np.array([62.28990701])
    x,y=q.ad2xy(a,d,tolerance=1e-1)
    print('x,y',x,y)


    x=np.array([87.71966066])
    y=np.array([924.73084299])
    #x=np.array([78.95992286])
    #y=np.array([937.7831667])
    a,d=q.xy2ad(x,y)
    print('a,d',a,d)

    rot,cdelt=q.getrot()
    print(rot,cdelt)

    area=q.pixelarea
    print(area)
