from dataclasses import dataclass
import numpy as np
import h5py



''' to define the potential columns in the tables WAV, XYG, etc... '''


@dataclass(frozen=True)
class H5Column(object):
    description: str
    dtype: type
        
    def flush(self):
        self=[]
        
    def reset(self,*args):
        if len(args)==1:
            self=list(args[0])
        else:
            self=[]

            
    @property
    def name(self):
        return self.__class__.__name__.lower()

    @property
    def to_numpy(self):
        return np.array(self,dtype=self.dtype)

    def astype(self,dtype):
        return np.array(self,dtype=dtype)




    
class XYG(list,H5Column):
    def __init__(self,*args,description='1d grism coordinates',dtype=np.uint32):
        H5Column.__init__(self,description,dtype)
        if len(args)==1:
            super(XYG,self).__init__(args[0])

class LAM(list,H5Column):
    def __init__(self,*args,description='wavelength indices',dtype=np.uint16):
        H5Column.__init__(self,description,dtype)
        if len(args)==1:
            super(LAM,self).__init__(args[0])
        
class WAV(list,H5Column):
    def __init__(self,*args,description='wavelengths in A',dtype=np.float32):
        H5Column.__init__(self,description,dtype)
        if len(args)==1:
            super(WAV,self).__init__(args[0])
        
class VAL(list,H5Column):
    def __init__(self,*args,description='values in the table',dtype=np.float64):
        H5Column.__init__(self,description,dtype)
        if len(args)==1:
            super(VAL,self).__init__(args[0])

'''
class PIX(list):
    def __init__(self,*args,description='direct image pixels',\
                 dtype=(np.uint16,np.uint16)):
        self.description=description
        self.dtype=dtype
    def write(self,h5):
        dtype=np.dtype([('x',np.uint16),('y',np.uint16)])
'''

        
if __name__=='__main__':
    
    xyg=XYG()
    q=[i for i in range(100)]
    

#    xyg.extend(q)
#    print(xyg)
#    with h5py.File('test.h5','w') as hf:
#        xyg.write(hf)
#
#        
#    with h5py.File('test.h5','r') as hf:
#        a=XYG()
#        a.load(hf)
#    
#    print(a)
