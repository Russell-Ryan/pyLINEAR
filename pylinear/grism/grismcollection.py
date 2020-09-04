from astropy.table import Table
from astropy.io import fits
import statistics as stats

from . import instruments
from ..utilities.ascii_files import read_ascii_table
from .grism import SimulatedFile,ObservedFile

class GrismCollection(object):
    def __init__(self,filename,observed=True):
        print('[info]Loading grism collection')
        
        self.files={}
        
        # load the images
        if observed:
            self.load_observed(filename)
        else:
            self.load_simulated(filename)

        # get the grism name
        grism=[g.grism for g in self]

            
        # do some quick error checking
        n=len(self)
        if n==0:
            print('[warn]No images are loaded')
        else:
            print('[info]Loaded {} images'.format(n))

            
    def __len__(self):
        return len(self.files)

    def __iter__(self):
        yield from self.files.values()

    def items(self):
        return self.files.items()
            
    def values(self):
        return self.files.values()

    
    def load_simulated(self,wcsfile):
        print('[info]Loading simulated grism images')
        names=('dataset','crval1','crval2','orientat','grism')

        tab,meta=read_ascii_table(wcsfile,names=names)

        # get the observational configuration as a tuple:
        obsconf={'telescope':meta['TELESCOPE'],
                 'instrument':meta['INSTRUMENT'],
                 'detector':meta['DETECTOR'],
                 'grism':'',
                 'blocking':meta['BLOCKING'],
                 'dataset':'',
                 'crvals':(0.,0.),
                 'orientat':0.}

        # get the detector information from my XML lookup table
        #detector=load_detector(*obsconf)
        insconf=instruments.Config(obsconf['telescope'])
        
        # interpret each row as a new file
        for dataset,crval1,crval2,orientat,grism in tab.iterrows():
            #crvals=(crval1,crval2)
            #grism=(grism,meta['BLOCKING'])

            obsconf['dataset']=dataset
            obsconf['crvals']=(crval1,crval2)
            obsconf['grism']=grism
            obsconf['orientat']=orientat

            self.files[dataset]=SimulatedFile(obsconf,insconf)

            #self.files[dataset]=SimulatedFile(dataset,crvals,orientat,
            #                                  grism,detector)

            
            
    def load_observed(self,fltfile):
        print('[info]Loading observed grism images')

        # read the table
        names=('filename',)    
        tab,meta=read_ascii_table(fltfile,names=names)

        
        # interpret each line as a new image
        for (filename,) in tab.iterrows():
            phdr=fits.getheader(filename,exten=0)


            # let's check the obstype, but assume the best of the user
            # I hope they don't make a fool of me.
            if phdr.get('OBSTYPE','SPECTROSCOPIC') == 'SPECTROSCOPIC':
                insconf=instruments.Config(phdr['TELESCOP'])
                img=ObservedFile(filename,insconf)
                self.files[img.dataset]=img
            else:
                print('[warn]Ignoring: {} not spectroscopy.'.format(filename))

    def get_default_extraction(self):
        lamb0,lamb1,dlamb=[],[],[]

        # could streamline the calculation of min/max for lamb1/lamb0,
        # respectively.  Then could consider a dlamb compuation that
        # forces dlamb to be an even factor of (lamb1-lamb0)
        
        for dataset in self:            
            grism=dataset.grism
            for device in dataset.detector:
                lamb0.append(device.grisms[grism].lamb0)
                lamb1.append(device.grisms[grism].lamb1)
                dlamb.append(device.grisms[grism].dlamb)

        # make the results a dict
        ext={'lamb0':max(lamb0),'lamb1':min(lamb1),'dlamb':stats.median(dlamb)}

        return ext

        # return as a tuple
        #return lamb0,lamb1,dlamb
            
