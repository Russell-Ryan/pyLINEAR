import numpy as np
#from astropy.io import fits
import h5py
import datetime

import h5axeconfig

from pylinear.astro import fitsimage
from pylinear.utilities import indices,Pool
from pylinear import grism,h5table




def cutoutWorker(flt,conf,grismconf,sources):
    ''' call the cutout routine '''

    path=conf['tables']['path']
    xpad,ypad=conf['padding']
    dset=flt.dataset
    filename='{}_cut.h5'.format(dset)
    
    with h5py.File(filename,'w') as h5Out,h5table.H5Table(dset,'DDT',path=path) as h5In:
        for detname,detimg in flt:
            h5detOut=h5Out.require_group(detname)
            h5detIn=h5In[detname]
            detconf=grismconf[detname]

            #sci,scihdr=flt.readfits(detconf.sciext,detconf.extver)
            sci=flt.readfits(detconf.sciext,detconf.extver)
            
            for beamname,beamconf in detconf:
                h5beamOut=h5detOut.require_group(beamname)
                h5beamIn=h5detIn[beamname]
                
                for segid,src in sources:
                    srcname=str(segid)
                    ddt=h5table.DDT(src.segid)
                    ddt.readH5(h5beamIn)
                    
                    xg,yg=indices.one2two(ddt.xyg,detimg.shape)
                    if len(ddt)>0:

                        x0=np.clip(np.amin(xg)-xpad-1,0,detimg.shape[1])
                        x1=np.clip(np.amax(xg)+xpad,0,detimg.shape[1])
                        y0=np.clip(np.amin(yg)-ypad-1,0,detimg.shape[0])
                        y1=np.clip(np.amax(yg)+ypad,0,detimg.shape[0])

                        sub=sci[y0:y1,x0:x1]
                        #hdr=scihdr.copy()
                        hdr=sci.header.copy()
                        hdr['NAXIS1']=x1-x0
                        hdr['NAXIS2']=y1-y0
                        hdr['CRPIX1']-=x0
                        hdr['CRPIX2']-=y0
                        hdr['LTV1']=-x0
                        hdr['LTV2']=-y0


                        
                        d=h5beamOut.create_dataset(srcname,data=sub,\
                                                   compression='gzip')
                        d.attrs['x0']=np.uint16(x0)
                        d.attrs['x1']=np.uint16(x1)
                        d.attrs['y0']=np.uint16(y0)
                        d.attrs['y1']=np.uint16(y1)



def cutout(conf,sources):
    if not conf['perform']:
        return
    print('[info]Starting Cutouts')

    # just a short-hand
    conffile=conf['calib']['h5conf']

    # load the grism images
    grisms=grism.Data(conf['imglst'],'img',conffile)

    # get the grism config data
    grismconf=h5axeconfig.Camera(conffile,grisms.grism,beams=conf['beam'])

    # pass the arguments that do not change
    args=(conf,grismconf,sources)

    # use my version of the pool
    p=Pool(ncpu=conf['cpu']['ncpu'])
    filenames=p(cutoutWorker,grisms.values,*args,prefix='Making Cutouts')
