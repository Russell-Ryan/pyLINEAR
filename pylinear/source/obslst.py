import os


from pylinear.utilities import asciitable
from pylinear.synthphot import Bandpass


class ObsLST(object):
    def __init__(self,conf):
        ''' load the observational catalog '''

        # read the obslst file
        #self.columns=['imgfile','bandpass','zeropoint']
        self.columns=['imgfile','bandpass']
        self.data=asciitable.AsciiTable(self.columns,filename=conf['obslst'])

        # load the filter curves into the bandpass column
        for i,(imgfile,bpname) in enumerate(self.data):
            self.data['bandpass'][i]=Bandpass(bpname)

        # set the detection band
        self.detindex=conf['detindex']
        
    def __iter__(self):
        for data in self.data:
            yield (*data,data[1].zeropoint)

        
    @property
    def detImage(self):
        return self.data['imgfile'][self.detindex]

    @property
    def detBandpass(self):
        return self.data['bandpass'][self.detindex]

    @property
    def detZeropoint(self):
        return self.data['bandpass'][self.detindex].zeropoint
    
    @property
    def detData(self):
        return self.data[self.detindex]
        
