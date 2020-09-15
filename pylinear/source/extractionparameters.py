import numpy as np

def validate(func):
    def wrapper(cls):
        # https://www.utf8-chartable.de/unicode-utf8-table.pl
        assert (cls.lamb0 is not None),'\u03BB\u2080 is None'
        assert (cls.lamb1 is not None),'\u03BB\u2081 is None'
        assert (cls.dlamb is not None),'\u0394\u03BB is None'
        assert (cls.lamb1 > cls.lamb0),'\u03BB\u2081\u2264\u03BB\u2080'
        return func(cls)
    return wrapper


class ExtractionParameters(object):
    FLOAT=np.float64
    INT=np.uint64

    def __init__(self,lamb0=None,lamb1=None,dlamb=None):
        self.lamb0=lamb0
        self.lamb1=lamb1
        self.dlamb=dlamb

    @validate
    def nwavelength(self):    
        n=np.ceil((self.lamb1-self.lamb0)/self.dlamb)+1
        return self.INT(n)

    @validate
    def wavelengths(self):
        l0=self.lamb0
        l1=self.lamb1+self.dlamb
        wave=np.arange(l0,l1,self.dlamb,dtype=self.FLOAT)
        return wave

    @validate
    def limits(self):
        l0=self.lamb0-0.5*self.dlamb
        l1=self.lamb1+1.5*self.dlamb
        return np.arange(l0,l1,self.dlamb,dtype=self.FLOAT)

        

if __name__=='__main__':
    #x=ExtractionParameters(lamb0=10.,lamb1=10.,dlamb=2)
    x=ExtractionParameters(1,11,2)
    print(x.nwavelength(),len(x.wavelengths()))
