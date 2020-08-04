import h5py
import numpy as np
import os

from .h5tablebase import H5TableBase

from .pdt import PDT
from .odt import ODT
from .omt import OMT

class H5Table(H5TableBase):

    def __init__(self,dataset,path=None,mode='a'):
        self.dataset=dataset
        self.name=dataset
        if path is None:
            path=os.getcwd()
        self.path=path

        if mode not in ['a','w-','x','r+','w','r']:
            raise NotImplementedError('invalid mode {}'.format(mode))
        self.mode=mode


    def add_device(self,dev,**kwargs):
        self.h5device=self.h5file.require_group(dev.name)
        self.h5device.attrs['NAXIS1']=np.uint16(dev.naxis1)
        self.h5device.attrs['NAXIS2']=np.uint16(dev.naxis2)
        
        
    def add_beam(self,beam):
        self.h5beam=self.h5device.require_group(beam)
        

    def add_ttype(self,ttype,**kwargs):
        self.h5table=self.h5beam.require_group(ttype)
        for k,v in kwargs.items():
            self.write_attribute(self.h5table,k,v)
            
    

    def open_table(self,devname,beamname,ttype):
        self.h5device=self.h5file[devname]
        self.h5beam=self.h5device[beamname]
        self.h5table=self.h5beam[ttype]
        
    def load_from_file(self,source,beam,ttype):

        if ttype=='odt':
            # get the wavelengths
            wav0=self.load_attribute(self.h5table,'wav0')
            wav1=self.load_attribute(self.h5table,'wav1')
            dwav=self.load_attribute(self.h5table,'dwav')
            wav=np.arange(wav0,wav1+dwav,dwav)
            
            tab=ODT(source.segid,beam,wav)
            for pixel,wht in zip(source.xyd,source.wht):
                pdt=PDT.load(pixel,self.h5table)
                pdt*=wht
                tab.extend(pdt)
        elif ttype=='omt':
            tab=OMT(source.segid,beam,self.h5table)        
        else:
            pass

        return tab
        
    def write_in_file(self,tab,**kwargs):
        tab.write_h5(self.h5table,**kwargs)

    @property
    def filename(self):
        return os.path.join(self.path,self.dataset)+'.h5'


    def __enter__(self):
        self.h5file=h5py.File(self.filename,self.mode)
        return self

    def __close__(self):
        if hasattr(self,'h5file'):
            self.h5file.close()

    def __exit__(self,exe_type,exc_val,exc_tb):
        self.__close__()

    def __del__(self,*args):
        self.__close__()

        
