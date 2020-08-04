import numpy as np



''' to define the potential columns in the tables WAV, XYG, etc... '''


class Column(list):
    def __init__(self,*args,desc=None,dtype=None):
        self.description=desc
        self.dtype=dtype
        if len(args)==1:
            self.extend(args[0])
           
        
    def reset(self,*args):
        if len(args)==1:
            self=list(args[0])
        else:
            self.clear()

    def __ge__(self,a):
        return self.to_numpy() >= a

    def __gt__(self,a):
        return self.to_numpy() > a

    def __le__(self,a):
        return self.to_numpy() <= a
  
    def __lt__(self,a):
        return self.to_numpy() < a
        
        
    def __imul__(self,a):
        v=self.to_numpy()*a
        self.clear()
        self.extend(v)
        return self


    def __itruediv__(self,a):
        v=self.to_numpy()/a
        self.clear()
        self.extend(v)
        return self
    
    
        
    @property
    def name(self):
        return self.__class__.__name__.lower()

    def to_numpy(self,g=None):
        v=np.array(self,dtype=self.dtype)
        if g is not None:
            v=v[g]
        return v
       
    def astype(self,dtype):
        return np.array(self,dtype=dtype)

class X(Column):
    def __init__(self,*args,description='x coordinate',dtype=np.uint16):
        Column.__init__(self,args,desc=description,dtype=dtype)

class Y(Column):
    def __init__(self,*args,description='y coordinate',dtype=np.uint16):
        Column.__init__(self,*args,desc=description,dtype=dtype)
            
class Count(Column):
    def __init__(self,*args,description='wavelength count',dtype=np.uint32):
        Column.__init__(self,*args,desc=description,dtype=dtype)
            
class XYG(Column):
    def __init__(self,*args,description='1d grism coordinates',dtype=np.uint32):
        Column.__init__(self,*args,desc=description,dtype=dtype)
     
class LAM(Column):
    def __init__(self,*args,description='wavelength indices',dtype=np.uint16):
        Column.__init__(self,*args,desc=description,dtype=dtype)
   
class WAV(Column):
    def __init__(self,*args,description='wavelengths in A',dtype=np.float32):
        Column.__init__(self,*args,desc=description,dtype=dtype)
     
class VAL(Column):
    def __init__(self,*args,description='values in the table',dtype=np.float64):
        Column.__init__(self,*args,desc=description,dtype=dtype)

        
if __name__=='__main__':
    v=VAL([1,2,3,4,5])
    v*=2
    print(v)
