import numpy as np
import multiprocessing as mp
import os
import pdb

from pylinear import h5table
from pylinear.h5table import h5utils
from pylinear.utilities import indices,Pool

TTYPE='DDT'

def makeODTs(grism,sources,grismconf,path,remake,nsub):
    # create the table
    tab=h5table.H5Table(grism.dataset,TTYPE,path=path)


    pixfrac=1.0   # DO NOT CHANGE THIS.  NOT YET UNDERSTOOD!
        
    # remake the table?
    if remake:
        if os.path.isfile(tab.filename):
            os.remove(tab.filename)
    else:
        return tab.filename
    
    # pixel based ------------------------------
    dx=np.array([0,0,1,1])            # HARDCODE
    dy=np.array([0,1,1,0])            # HARDCODE
    #-------------------------------------------

    # open the file
    with tab as h5:

        # add some stuff to that header
        h5utils.writeAttr(h5,'segmap',sources.segmap)
        h5utils.writeAttr(h5,'nsource',np.uint16(len(sources)))
        h5utils.writeAttr(h5,'detimage',sources.obsdata.detImage)
        h5utils.writeAttr(h5,'detband',sources.obsdata.detName)
        h5utils.writeAttr(h5,'maglimit',np.float32(sources.maglimit))
        
        
        # process each detector
        for detname,detconf in grismconf:
            
            detgrp=h5.require_group(detname)

            # add some attributes to this
            detgrp.attrs['naxis1']=np.uint16(detconf.naxis[0])
            detgrp.attrs['naxis2']=np.uint16(detconf.naxis[1])
            
            # get the center of the detector
            xc,yc=detconf.naxis/2.
            
            # get this grism image
            thisGrism=grism[detname]

            
            # the pixel area of this detector
            detpixelarea=thisGrism.pixelarea

            for beam,beamconf in detconf:
                beamgrp=detgrp.require_group(beam)
                if remake:
                    sourcesDone=[]
                else:
                    sourcesDone=list(beamgrp.keys())

                    
                #if beam in detgrp:
                #    beamgrp=detgrp[beam]
                #    sourcesDone=list(beamgrp.keys())
                #else:
                #    beamgrp=detgrp.create_group(beam)
                #    sourcesDone=[]

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

                # put some stuff in the table
                h5utils.writeAttr(beamgrp,'wav0',np.float32(wav[0]))
                h5utils.writeAttr(beamgrp,'wav1',np.float32(wav[-1]))
                h5utils.writeAttr(beamgrp,'dwav',np.float32(dwav))

                # process each source
                for segid,src in sources:
                    if src.name not in sourcesDone:  # only process new sources

                        
                        # compute ratio of pixel area between
                        # the FLT and the source
                        pixrat=detpixelarea/(pixfrac*src.pixelarea)

                        # make an ODT
                        odt=h5table.ODT(src.segid,wav=wav)

                        # process each pixel in the source
                        for xd,yd,wd in src:
                            # convert the corners of the direct image to the
                            # corresponding grism image
                            xg,yg=src.xy2xy(xd+dx,yd+dy,thisGrism)
                           

                            
                            # disperse those corners
                            xyg,lam,val=beamconf.specDrizzle(xg,yg,wav,
                                                             pixfrac=pixfrac)


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
                            xyc=np.float32(src.xyc-src.ltv)
                            

                            if TTYPE=='ODT':
                                odt.writeH5(beamgrp,RA=src.adc[0],\
                                            Dec=src.adc[1],\
                                            xc=xyc[0],yc=xyc[1],\
                                            mag=np.float32(src.mag),\
                                            area=np.float32(src.area),\
                                            npix=np.uint32(src.npix))
                            elif TTYPE=='DDT':

                                
                                ddt=odt.decimate(thisGrism.npix)
                                ddt.writeH5(beamgrp,RA=src.adc[0],\
                                            Dec=src.adc[1],\
                                            xc=xyc[0],yc=xyc[1],\
                                            mag=np.float32(src.mag),\
                                            area=np.float32(src.area),\
                                            npix=np.uint32(src.npix))

                                
                            else:
                                raise NotImplementedError("invalid table type")
                                        
                            
    return tab.filename


def makeOMTs(flt,sources,grismconf,path,remake,nsub):
    #print("[info]Making the OMTs")
    # create the table
    tab=h5table.H5Table(flt.dataset,'omt',path=path)


    # remake the table?
    if remake:
        if os.path.isfile(tab.filename):
            os.remove(tab.filename)
    else:
        return tab.filename

    with tab as h5:

        # add some stuff to that header
        h5utils.writeAttr(h5,'segmap',sources.segmap)
        h5utils.writeAttr(h5,'nsource',np.uint16(len(sources)))
        h5utils.writeAttr(h5,'detimage',sources.obsdata.detImage)
        h5utils.writeAttr(h5,'detband',sources.obsdata.detName)
        h5utils.writeAttr(h5,'maglimit',np.float32(sources.maglimit))


        for detname,detconf in grismconf:

            detgrp=h5.require_group(detname)

            # add some attributes to this
            detgrp.attrs['naxis1']=np.uint16(detconf.naxis[0])
            detgrp.attrs['naxis2']=np.uint16(detconf.naxis[1])
            
            # get the center of the detector
            xc,yc=detconf.naxis/2.
            thisGrism=flt[detname]
                
            for beam,beamconf in detconf:
                beamgrp=detgrp.require_group(beam)
                if remake:
                    sourcesDone=[]
                else:
                    sourcesDone=list(beamgrp.keys())
                    
                    
                #if beam in detgrp:
                #    beamgrp=detgrp[beam]
                #    sourcesDone=list(beamgrp.keys())
                #else:
                #    beamgrp=detgrp.create_group(beam)
                #    sourcesDone=[]

                wav=beamconf.wavelengths(xc,yc,1)      # force nsub=1

                # add some stuff to table
                h5utils.writeAttr(beamgrp,'wav0',np.float32(wav[0]))
                h5utils.writeAttr(beamgrp,'wav1',np.float32(wav[-1]))
                h5utils.writeAttr(beamgrp,'dwav',np.float32(wav[1]-wav[0]))

                # process each source
                for segid,src in sources:
                    if src.name not in sourcesDone:
                        
                        xd,yd=src.convexHull
                        xg,yg=src.xy2xy(xd,yd,thisGrism)
                                                
                        xyg,lam,val=beamconf.specDrizzle(xg,yg,wav)
                        if len(xyg)!=0:
                            xyc=np.float32(src.xyc-src.ltv)
                            omt=h5table.OMT(segid)
                            xyg=indices.unique(np.array(xyg))
                            omt.extend(xyg)
                            omt.writeH5(beamgrp,RA=src.adc[0],\
                                        Dec=src.adc[1],\
                                        xc=xyc[0],yc=xyc[1],\
                                        mag=np.float32(src.mag),\
                                        area=np.float32(src.area),\
                                        npix=np.uint32(src.npix))

    return tab.filename

def tabulate(conf,grisms,sources,grismconf,ttype):
    
    # check the beams existing
    if len(grismconf.beams)==0:
        print('[warn]No beams to tabulate.')
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
    p=Pool(ncpu=conf['cpu']['ncpu'])
    prefix='Making {}s'.format(ttype.upper())
    filenames=p(func,grisms.values,*args,prefix=prefix)

        
    return filenames
    
