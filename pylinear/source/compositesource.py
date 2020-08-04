import numpy as np

from ..wcs import WCS
from .extractionparameters import ExtractionParameters


class CompositeSource(WCS,ExtractionParameters):



    def __init__(self,segid,seg,lamb0=None,lamb1=None,dlamb=None):

        # initialize the WCS
        WCS.__init__(self,seg.header)

        # set the extraction parameters
        ExtractionParameters.__init__(self,
                                      lamb0=seg.get('LAMB0',None),
                                      lamb1=seg.get('LAMB1',None),
                                      dlamb=seg.get('DLAMB',None))
        if lamb0 is not None: self.lamb0=lamb0
        if lamb1 is not None: self.lamb1=lamb1
        if dlamb is not None: self.dlamb=dlamb

        self.sources={}

        #print(self.shape)
    def __len__(self):
        return len(self.sources)

    def __setitem__(self,k,v):
        self.sources[k]=v

    def __getitem__(self,k):
        return self.sources[k]

    def __iter__(self):
        yield from self.sources.values()
    
    def items(self):
        yield from self.sources.items()

        




    
