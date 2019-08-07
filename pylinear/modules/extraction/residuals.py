import numpy as np
from astropy.io import fits

from pylinear.utilities import gzip,indices

def computeResiduals(conf,grisms,grismconf,mat,results):
    if not conf['perform']:
        return
    print("[info]computing the residuals")
    
    # compute the model
    model=mat.A.matvec(result.x)

    # get the image and xy indices
    imgindex,pixindex=divmod(mat.iuniq,mat.npix)
    index=0        # a counter
    for fltfile,flt in grisms:
        # make some output array
        hdul=fits.HDUList()

        # process each detector within the FLT
        for detname,det in flt:
            detconf=grismconf[detname]

            # get the pixels if there are some valid ones
            g=np.where(imgindex==index)[0]
            if len(g)!=0:
                # read the images
                sci,scihdr=flt.readfits(detconf.sciext,detconf.extver)
                unc,unchdr=flt.readfits(detconf.sciext,detconf.extver)
                dtype=np.dtype(sci.dtype.name)


                # make a zeroth extension
                hdr=fits.Header()
                hdul.append(fits.PrimaryHDU(header=hdr))

                # put the science image in for safe keeping
                hdul.append(fits.ImageHDU(data=sci,header=scihdr))
                                
                # make a model image
                mod=np.zeros_like(sci)
                modhdr=det.mkhdr(dtype,extname='MOD',extver=detconf.extver)

                # get teh (x,y)                
                x,y=indices.one2two(pixindex[g],det.naxis)
                mod[y,x]=(model[g]*unc[y,x])
                hdul.append(fits.ImageHDU(data=mod,header=modhdr))
                
                # make the residual image
                res=sci-mod
                reshdr=det.mkhdr(dtype,extname='RES',extver=detconf.extver)
                hdul.append(fits.ImageHDU(data=res,header=reshdr))

                
                
        outfile='{}_res.fits'.format(flt.dataset)
        hdul.writeto(outfile,overwrite=True)
        if conf['gzip']:
            gzip.gzip(outfile)
    

        index+=1
