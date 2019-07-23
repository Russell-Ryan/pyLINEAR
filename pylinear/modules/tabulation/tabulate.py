import numpy as np
import multiprocessing as mp
import os


#from pylinear import h5table,h5utils
#from pylinear.h5table import h5table,h5utils
from pylinear import h5table
from pylinear.h5table import h5utils
from pylinear.utilities import indices,pool


def detGroup(h5,det,detconf):
    if det in h5:
        detgrp=h5[det]
    else:
        detgrp=h5.create_group(det)
    return detgrp


def makeODTs(grism,sources,grismconf,path,remake,nsub):
    
    # create the table
    tab=h5table.H5Table(grism.dataset,'ddt',path=path)

    # remake the table?
    if remake and os.path.isfile(tab.filename):
        os.remove(tab.filename)

        
    # pixel based ------------------------------
    dx=np.array([0,0,1,1])            # HARDCODE
    dy=np.array([0,1,1,0])            # HARDCODE
    #-------------------------------------------

    with tab as h5:        
        for det,detconf in grismconf:

            detgrp=detGroup(h5,det,detconf)
            
            #if det in h5:
            #    detgrp=h5[det]
            #else:
            #    detgrp=h5.create_group(det)

            
            # get the center of the detector
            xc,yc=detconf.naxis/2.
            
            # get this grism image
            thisGrism=grism[det]

            # the pixel area of this detector
            detpixelarea=thisGrism.pixelarea

            for beam,beamconf in detconf:
                if beam in detgrp:
                    beamgrp=detgrp[beam]
                    sourcesDone=list(beamgrp.keys())
                else:
                    beamgrp=detgrp.create_group(beam)
                    sourcesDone=[]

                # compute the set difference
                #segids=[src.name for src in sources]
                #done=list(beamgrp.keys())
                #toDo=segids-done

                    
                # get the ODT wavelenegths.  NOTE: This are *NOT* the
                # same as the extraction wavelengths due to NSUB.
                # here using center of detector.  Could improve this by
                # putting inside loop on sources and take (xc,yc)
                # from the source.  This is just faster and doesn't
                # seem to be a problem just yet
                wav=beamconf.wavelengths(xc,yc,nsub)  
                dwav=wav[1]-wav[0]

                for segid,src in sources:
                    if src.name not in sourcesDone:  # only process new sources
                        
                        # compute ratio of pixel area between
                        # the FLT and the source
                        pixrat=detpixelarea/src.pixelarea

                        # make an ODT
                        odt=h5table.ODT(src.segid,wav=wav)
                        
                        # process each pixel in the source
                        for xd,yd,wd in src:
                            # convert the corners of the direct image to the
                            # corresponding grism image
                            xg,yg=src.xy2xy(xd+dx,yd+dy,thisGrism)

                            # disperse those corners
                            xyg,lam,val=beamconf.specDrizzle(xg,yg,wav)
                            if len(xyg)!=0:
                                
                                # create the PDT
                                pix=(int(xd-src.ltv[0]),int(yd-src.ltv[1]))
                                pdt=h5table.PDT(pix)
                                pdt.extend(xyg,lam,val)
                                
                                # scale the PDT by:
                                # 1. direct image weight (wd),
                                # 2. ratio of pixel areas between seg & FLT
                                # 3. wavelength sampling (trapezoidal rule)
                                pdt*=(wd*pixrat*dwav)

                                # append the PDT
                                odt.extend(pdt)

                        # if ODT is valid, then write it!
                        if len(odt)!=0:
                            ddt=odt.decimate()
                            
                            ddt.writeH5(beamgrp,RA=src.adc[0],Dec=src.adc[1],\
                                        xc=src.xyc[0],yc=src.xyc[1],\
                                        mag=src.mag,area=src.area,npix=src.npix)
                                        
                            
    return tab.filename


def makeOMTs(flt,sources,grismconf,path,remake,nsub):
    print("making the OMTs")
    # create the table
    tab=h5table.H5Table(flt.dataset,'omt',path=path)

    # remake the table?
    if remake and os.path.isfile(tab.filename):
        os.remove(tab.filename)

    with tab as h5:
        for det,detconf in grismconf:
            if det in h5:
                detgrp=h5[det]
            else:
                detgrp=h5.create_group(det)

            # get the center of the detector
            xc,yc=detconf.naxis/2.
            thisGrism=flt[det]
                
            for beam,beamconf in detconf:
                if beam in detgrp:
                    beamgrp=detgrp[beam]
                    sourcesDone=list(beamgrp.keys())
                else:
                    beamgrp=detgrp.create_group(beam)
                    sourcesDone=[]
                    
                wav=beamconf.wavelengths(xc,yc,1)      # force nsub=1

                for segid,src in sources:
                    if src.name not in sourcesDone:
                        
                        xd,yd=src.convexHull
                        xg,yg=src.xy2xy(xd,yd,thisGrism)
                        xyg,lam,val=beamconf.specDrizzle(xg,yg,wav)
                        if len(xyg)!=0:
                            omt=h5table.OMT(segid)
                            xyg=indices.unique(np.array(xyg))
                            omt.extend(xyg)
                            omt.writeH5(beamgrp)
    return tab.filename

def tabulate(conf,grisms,sources,grismconf,ttype):
    
    # check the beams existing
    if len(grismconf.beams)==0:
        print('no beams to tabulate.')
        return

    
    # figure out which worker function to call
    ttype=ttype.lower()
    if ttype=='odt':
        func=makeODTs
    elif ttype == 'omt':
        func=makeOMTs
    else:
        raise NotImplementedError("Table type ({}) not found.".format(ttype))
  
    # arguments that do not change
    args=(sources,grismconf,conf['path'],conf['remake'],conf['nsub'])

    # run the code
    #q=[func(flt,*args) for name,flt in grisms]
    pool.pool(func,grisms.values(),*args,ncpu=conf['cpu']['ncpu'])

    
