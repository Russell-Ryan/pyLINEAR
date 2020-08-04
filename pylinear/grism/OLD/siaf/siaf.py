import h5py
import pysiaf
#from pysiaf.rotations import attitude
#from pysiaf.utils.rotations import pointing
from astropy.io import fits
import numpy as np
import os

class SIAF(dict):
    def __init__(self,telescope,aperture,siaffile=None):
        if siaffile is None:
            path=os.path.dirname(__file__)
            if path=='':
                path='.'
            siaffile=path+os.sep+'siaf.h5'
                
            
        self.siaffile=siaffile
        with h5py.File(self.siaffile,'r') as h5:
            ht=h5[telescope.upper()]
            ha=ht[aperture.upper()]

            for k,v in ha.attrs.items():
                setattr(self,k.lower(),v)

            for tok in ['A','B','AP','BP']:
                d,o=self.get_sip(ha,tok)
                setattr(self,'{}_order'.format(tok.lower()),o)
                setattr(self,tok.lower(),d)
                
            #self.sip={tok: self.get_sip(ha,tok) for tok in ['A','B','AP','BP']}
            

            
    def make_header(self,crval1,crval2,orientat,refsiaf=None):
        if refsiaf is None:
            refsiaf=self
        # based on what Bryan Hilbert said, I should probably transform
        # orientat to a local_roll, but that is really complicated and
        # makes very small differences
        A = pysiaf.rotations.attitude(refsiaf.v2, refsiaf.v3, 
                                      crval1, crval2, orientat)

        # compute the new positions
        crvals = pysiaf.utils.rotations.pointing(A, self.v2, self.v3)

        # compute the position angle
        pa=-orientat#-self.v3y
        print(self.v3y)
        # make a rotation matrix
        cs=np.cos(pa*np.pi/180)
        sn=np.sin(pa*np.pi/180)
        R=np.array([[cs,-sn],[sn,cs]])        

        # create a pixel matrix
        P=np.array([[-self.xscl/3600.,0],[0,self.yscl/3600.]],dtype=np.float64)

        # compute CD matrix
        cd=np.dot(P,R)
                
        # make a fits header
        hdr=fits.Header()
        hdr['NAXIS1']=(self.naxis1,'number of pixels in x')
        hdr['NAXIS2']=(self.naxis2,'number of pixels in y')
        hdr['CRPIX1']=(self.crpix1,'x-coordinate of reference pixel')
        hdr['CRPIX2']=(self.crpix2,'y-coordinate of reference pixel')
        hdr['CRVAL1']=(crvals[0],'first axis value at reference pixel')
        hdr['CRVAL2']=(crvals[1],'second axis value at reference pixel')        
        hdr['CD1_1']=(cd[0,0],'partial of first axis coordinate w.r.t. x')
        hdr['CD1_2']=(cd[1,0],'partial of first axis coordinate w.r.t. y')
        hdr['CD2_1']=(cd[0,1],'partial of second axis coordinate w.r.t. x')
        hdr['CD2_2']=(cd[1,1],'partial of second axis coordinate w.r.t. y')
        hdr['CTYPE1']=('RA---TAN-SIP','the coordinate type for the first axis')
        hdr['CTYPE2']=('DEC--TAN-SIP','the coordinate type for the second axis')
        hdr['EQUINOX']=(2000.,'equinox of coordinates')
        hdr['LATPOLE']=(90.,' ')
        hdr['LONGPOLE']=(180.,' ')
        hdr['ORIENTAT']=(orientat,'position angle of image y axis (deg. e of n)')
        for tok in ['a','b','ap','bp']:
            self.put_sip(hdr,tok)

        return hdr
        
    def put_sip(self,hdr,tok):
        
        dat=getattr(self,tok)
        if dat is not None:
            hdr['{}_order'.format(tok)]=getattr(self,'{}_order'.format(tok))
            label='{}_{}_{}'
            for k,v in dat.items():
                hdr[label.format(tok,k[0],k[1])]=v
        
            
    def get_sip(self,h5,tok):
        if tok in h5:
            dset=h5[tok]
            o=dset.attrs['order']
            d={(i,j): v for (i,j,v) in dset[:]}
        else:
            o=0
            d=None
        return d,o

if __name__=='__main__':
    x=SIAF('hst','wfc3ir')
    h=x.make_header(53.,-27.,156.199)
    print(h)
        
