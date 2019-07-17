import os
from collections import OrderedDict
from astropy.io import fits


class GrismImage(object):
    def __init__(self,name,filename=False):
        if filename:
            self.path,name=os.path.split(name)
            self.dataset=os.path.basename(name).split('_flt.fits')[0]
        else:
            self.path=''
            self.dataset=name

        self.gzip=os.path.splitext(name)[1]=='.gz'
        self.phdu=fits.Header()
        self.detectors=OrderedDict()

    def __iter__(self):
        for k,v in self.detectors.items():
            yield k,v

    def __setitem__(self,k,v):
        self.phdu[k]=v

    def __getitem__(self,k):
        return self.detectors[k]
        
    def __str__(self):
        return 'grism image'
    
    @property
    def filename(self):
        suf='.gz' if self.gzip else ''
        filename='{}_flt.fits{}'.format(self.dataset,suf)
        return os.path.join(self.path,filename)

    def keyword(self,key):
        return self.phdu[key]
