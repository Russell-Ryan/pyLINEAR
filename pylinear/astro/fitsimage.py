from astropy.io import fits
import numpy as np

from . import wcs
#import wcs

class FitsImage(wcs.WCS):
    def __init__(self,*args,extension=0):
        self.img=None
        self.hdr=None

        if len(args) !=0:
            if isinstance(args[0],str):
                filename=args[0]
                with fits.open(filename) as hdul:
                    self.loadHDU(hdul[extension])

                     

            
    def loadHDU(self,hdu):
        self.img=hdu.data
        self.hdr=hdu.header
        wcs.WCS.__init__(self,self.hdr)
        
    @property
    def data(self):
        return self.img
    
    @property
    def header(self):
        return self.hdr

    def __str__(self):
        return "fits image: {}x{} pix2\n".format(self.naxis[0],self.naxis[1])
    
    def __contains__(self,key):
        return key in self.hdr
        
    def __eq__(self,val):
        if isinstance(val,(int,float)):
            return self.img==val  
                    
    def __setitem__(self,key,value):
        self.hdr[key]=value

    def __getitem__(self,key):
        return self.hdr[key]

    def pixelValue(self,x,y):
        return self.dat[y,x]


    def extract(self,x0,x1,y0,y1,filename=None):
        
        # update
        x1+=1
        y1+=1

        # trim to be in the range
        x0=np.clip(x0,0,self.naxis[0])
        x1=np.clip(x1,0,self.naxis[0])
        y0=np.clip(y0,0,self.naxis[1])
        y1=np.clip(y1,0,self.naxis[1])

        # copy over the data and the header
        img=self.img[y0:y1,x0:x1]
        hdr=self.hdr.copy()

        # update the new header keywords
        hdr['NAXIS1']=x1-x0
        hdr['NAXIS2']=y1-y0
        hdr['CRPIX1']-=x0
        hdr['CRPIX2']-=y0
        hdr['LTV1']=-x0
        hdr['LTV2']=-y0

        # create the new data to return
        new=fits.HDUList()
        ext=fits.PrimaryHDU(img)
        ext.header=hdr
        new.append(ext)


        # write file to disk?
        if filename is not None:
            new.writeto(filename,overwrite=True)
            
        # create output in same datatype
        out=FitsImage()
        out.loadHDU(new[0])

        return out

    def writeto(self,filename,overwrite=True):
        self.hdu.writeto(filename,overwrite=overwrite)

if __name__=='__main__':
    filename='/Users/rryan/figs_gn1_wfc3_ir_f160w_030mas_drz_patch_v1ns.fits'


    a=FitsImage(filename)
    
    b=a.extract(50,100,70,90)
    print(b)
    

    
