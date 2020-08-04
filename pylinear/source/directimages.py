from astropy.table import Table

#from ..synthphot import Bandpass
from ..sedphot import Bandpass



class DirectImages(dict):
    def __init__(self,obscat,detindex=0):
        print('[info]Loading an observational catalog')
        self.detindex=detindex


        colnames=('imgfile','filtfile')
        tab=Table.read(obscat,names=colnames,format='ascii.no_header')

        for imgfile,filtroot in tab.iterrows():
            self[imgfile]=Bandpass.load(filtroot)

        if len(self)<self.detindex:
            raise RuntimeError("Detection index is out of range.")


        
    @property
    def filenames(self):
        return list(self.keys())

    @property
    def bandpasses(self):
        return list(self.values())    

    @property
    def detection_parameters(self):
        detfile=self.detfile
        detband=self.detband
        detzero=self.detzero
        return detfile,detband,detzero
    
    @property
    def detfile(self):
        return self.filenames[self.detindex]
    
    @property
    def detband(self):
        return self[self.detfile]

    @property
    def detzero(self):
        return self[self.detfile].zeropoint

    

    
