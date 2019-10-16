import numpy as np
#from astropy.io import fits
import h5py
import datetime

import h5axeconfig

from pylinear.utilities import Pool
from pylinear import grism


def worker(flt,grismconf,sources,padding):
    ''' call the cutout routine '''

    pass
    






def cutout(conf,sources):
    if not conf['perform']:
        return

    # just a short-hand
    calfile=conf['calib']['h5conf']

    # load the grism images
    grisms=grism.Data(conf['imglst'],conf['imgtype'],calfile)

    # get the grism config data
    grismconf=h5axeconfig.Camera(calfile,grisms.grism,beams=conf['beam'])

    # pass the arguments that do not change
    args=(grismconf,sources,conf['padding'])

    # use my version of the pool
    p=Pool(ncpu=conf['cpu']['ncpu'])
    filenames=p(cutoutWorker,grisms.values,*args,prefix='Cuting images')
