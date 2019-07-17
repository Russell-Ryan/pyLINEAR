from collections import OrderedDict

import h5axeconfig

from .grismimage import GrismImage
from .detector import Detector


class SimulatedGrism(GrismImage):
    filetype='simulated'

    def __init__(self,dataset,crvals,orientat,siaffile):

        GrismImage.__init__(self,dataset)

        # put some stuff in the PDHU
        
        
        
        # read the SIAF
        siaf=h5axeconfig.SIAF(siaffile)
        
        # load the images from the SIAF
        for detname,detconf in siaf:

            hdr=detconf.mkhdr(crvals,orientat)

            self.detectors[detname]=Detector(hdr)
            
