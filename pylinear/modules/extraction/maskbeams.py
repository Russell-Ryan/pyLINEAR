import numpy as np
import h5axeconfig

from ..tabulation import tabulate
from pylinear import h5table



def maskbeams(conf,extconf,grisms,sources=None):

    if sources is None:
        print('[debug]re-read the sources here, since the limits are different')
        
    
    calconf=conf['calib']
    conffile=calconf['h5conf']

    maskmag=26.    # magnitude limit to apply to mask
    mskconf=h5axeconfig.Camera(conffile,grisms.grism,beams=conf['mask'])
    tabulate(conf['tables'],grisms,sources,mskconf,'omt')

    
    # get the maximum sensitivity and dispersion
    sens=0.
    disp=0.
    for detname,detconf in extconf:
        xyc=tuple(s/2. for s in detconf.naxis)
        for beamname,beamconf in detconf:
            disp=max(disp,beamconf.dispersion(*xyc))
            sens=max(sens,beamconf.sensitivity.average)
                         
                         



    # update the DQAs for the grisms
    path=conf['tables']['path']
    for fltname,flt in grisms:
        with h5table.H5Table(flt.dataset,'omt',path=path) as h5:
            for detname,detconf in mskconf:
                h5det=h5[detname]
                maskXYG=set()
                for beamname,beamconf in detconf:
                    h5beam=h5det[beamname]
                    
                    thisSens=beamconf.sensitivity.average
                    dmag1=-2.5*np.log10(sens/thisSens)
                    for segid,src in sources:
                        thisDisp=beamconf.dispersion(*src.xyc)[0]
                        dmag2=-2.5*np.log10(disp/thisDisp)
                        
                        #dmag=-2.5*np.log10((disp/thisDisp)*(sens/thisSens))
                        maglim=maskmag+dmag1+dmag2
                        
                        
                        if src.mag<maglim:
                            omt=h5table.OMT(segid)
                            omt.readH5(h5beam)
                            if len(omt) != 0:
                                thisXYG=set(omt.xyg)
                                maskXYG=maskXYG.union(thisXYG)
                if len(maskXYG)!=0:
                    maskXYG=np.array(list(maskXYG),dtype=np.uint32)
                    grisms[fltname][detname].extendBPX(maskXYG)
