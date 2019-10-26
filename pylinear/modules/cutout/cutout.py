import numpy as np
import h5py
import datetime

import h5axeconfig

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
                                        
                    if len(ddt)>0:
                        xg,yg=indices.one2two(ddt.xyg,detimg.shape)
                        x0,x1=np.amin(xg)-xpad,np.amax(xg)+xpad
                        y0,y1=np.amin(yg)-ypad,np.amax(yg)+ypad

                        # cut the stamp
                        sub=sci.extract(x0,x1,y0,y1)
                                                
                        # write the file to disk
                        d=h5beamOut.create_dataset(srcname,data=sub.image,\
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
