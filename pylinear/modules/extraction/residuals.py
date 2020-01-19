import numpy as np
from astropy.io import fits
import pdb

from pylinear.utilities import gzip,indices

def gzip(conf,grisms):
    if not conf['perform']:
        return
    if conf['gzip']:
        print('[info]Zipping residual images')
        for fltfile,flt in grisms.items():
            gzip.gzip(residualName(flt))
        


def residualName(flt):
    outfile='{}_res.fits'.format(flt.dataset)
    return outfile

    
def create(conf,grisms,grismconf):
    if not conf['perform']:
        return
    print('[info]Preparing residual images')


    for fltfile,flt in grisms.items():
        # make some output array
        hdul=fits.HDUList()

        # process each detector within the FLT
        for detname,det in flt:
            detconf=grismconf[detname]
        
            # 0th Extensions:
            hdr=fits.Header()
            hdul.append(fits.PrimaryHDU(header=hdr))

            # 1st Extensions: the science image
            sci=flt.readfits(detconf.sciext,detconf.extver)
            hdul.append(sci.ImageHDU())
            dtype=np.dtype(sci.dtype.name)


            #sci,scihdr=flt.readfits(detconf.sciext,detconf.extver)
            #hdul.append(fits.ImageHDU(data=sci,header=scihdr))  
            #dtype=np.dtype(sci.dtype.name)

            # 2nd Extensions: the model image
            #mod=np.zeros_like(sci)
            mod=np.zeros_like(sci.image)
            modhdr=det.mkhdr(dtype,extname='MOD',extver=detconf.extver)
            hdul.append(fits.ImageHDU(data=mod,header=modhdr))


            # 3rd Extensions: the residual image
            res=sci-mod
            reshdr=det.mkhdr(dtype,extname='RES',extver=detconf.extver)
            hdul.append(fits.ImageHDU(data=res,header=reshdr))            

        hdul.writeto(residualName(flt),overwrite=True)


        
def update(conf,grisms,grismconf,mat,result,dqamask):
    if not conf['perform']:
        return
    print("[info]Updating residual images")
    
    # compute the model
    model=mat.A.matvec(result.x)

    # bits to mask
    #print('[debug]Hardcoding bitmask for WFC3/IR, omitting 512 bit')
    #bitmask=0b0000110111111111
    #dqamask=int(bitmask)
    #dqamask=1+2+4+8+16+32+64+128+256+1024+2048
    
    # get the image and xy indices
    imgindex,pixindex=divmod(mat.iuniq,mat.npix)
    index=0        # a counter
    for fltfile,flt in grisms.items():

        with fits.open(residualName(flt),mode='update') as hdul:

            # process each detector within the FLT
            for i,(detname,det) in enumerate(flt):
                detconf=grismconf[detname]

                # get the pixels if there are some valid ones
                g=np.where(imgindex==index)[0]
                if len(g)!=0:

                    # some stuff to ensure the file is properly written
                    sciext=3*i+1
                    modext=3*i+2
                    resext=3*i+3
                    
                    # read the images
                    sci=flt.readfits(detconf.sciext,detconf.extver)
                    unc=flt.readfits(detconf.uncext,detconf.extver)
                    dqa=flt.readfits(detconf.dqaext,detconf.extver)
                    
                    # get the (x,y) pairs
                    x,y=indices.one2two(pixindex[g],det.shape)

                    # update the model
                    hdul[modext].data[y,x]+=(model[g]*unc[y,x])
                    
                    # update the residual image
                    hdul[resext].data[y,x]=sci[y,x]-hdul[modext].data[y,x]
                    
                    # remove pixels in the DQAs
                    #g=np.where(np.bitwise_and(dqa,dqamask) != 0)[0]
                    g=np.where(np.bitwise_and(dqa.image,dqamask) != 0)[0]
                    #hdul[resext].data[g]=np.nan
                    print("[warn]MUST FIX BITMASKING")

            print(hdul[resext].data[y,x])
            print(residualName(flt))
            hdul.writeto(residualName(flt),overwrite=True)      
        # update the counter
        index+=1
