import numpy as np
import h5axeconfig

from ..tabulation import tabulate
from pylinear import h5table



def maskbeams(conf,extconf,grisms,sources=None):

    if sources is None:
        print('[debug]re-read the sources here, since the limits are different')
        
    # set some things from the user configuration        
    calconf=conf['calib']
    conffile=calconf['h5conf']
    maskmag=26.    # magnitude limit to apply to mask


    # load the beams to mask
    mskconf=h5axeconfig.Camera(conffile,grisms.grism,beams=conf['mask'])

    # make the mask tables (if need-be)
    tabulate(conf['tables'],grisms,sources,mskconf,'omt')

    
    # get the maximum sensitivity and dispersion for the extraction beams
    sens=0.
    disp=0.
    for detname,detconf in extconf:
        xyc=tuple(s/2. for s in detconf.naxis)
        for beamname,beamconf in detconf:
            extDisp=max(disp,beamconf.dispersion(*xyc))
            extSens=max(sens,beamconf.sensitivity.average)
                         
                         



    # update the DQAs for the grisms
    path=conf['tables']['path']
    for fltname,flt in grisms:


        # could put the following in multiprocessing
        with h5table.H5Table(flt.dataset,'omt',path=path) as h5:
            for detname,detconf in mskconf:
                h5det=h5[detname]

                maskXYG=set()      # something to collect the pixels
                for beamname,beamconf in detconf:
                    h5beam=h5det[beamname]
                    
                    # compute a change to the sensitivity
                    thisSens=beamconf.sensitivity.average
                    dmag1=-2.5*np.log10(extSens/thisSens)
                    for segid,src in sources:
                        thisDisp=beamconf.dispersion(*src.xyc)[0]
                        dmag2=-2.5*np.log10(extDisp/thisDisp)

                        # update the masking magnitude limit:
                        maglim=maskmag+dmag1+dmag2
                        
                        # only keep the source if in the limit (this will
                        # change when I put in extra source reading)
                        if src.mag<maglim:
                            
                            # load the OMT
                            omt=h5table.OMT(segid)
                            omt.readH5(h5beam)
                            if len(omt) != 0:
                                # update the masking pixels
                                maskXYG=maskXYG.union(set(omt.xyg))
                                
                if len(maskXYG)!=0:

                    # if there are pixels to mask, then update the grism
                    # image DQAs
                    maskXYG=np.array(list(maskXYG),dtype=np.uint32)
                    grisms[fltname][detname].extendBPX(maskXYG)


    print('done.')
    q=input()
