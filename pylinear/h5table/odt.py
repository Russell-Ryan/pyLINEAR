import numpy as np
import h5py


from .h5utils import H5Utils
from .pdt import PDT
from .ddt import DDT
from . import columns


class ODT(H5Utils):
    DTYPE=np.uint64         # for internal integer arithmetic

    
    def __init__(self,segid,wav=[]):
        self.segid=segid

        self.wav=columns.WAV(wav)
        self.xyg=columns.XYG()
        self.lam=columns.LAM()
        self.val=columns.VAL()
        
        self.pix=[]
        self.count=[0]

    
    def extend(self,pdt):
        assert isinstance(pdt,PDT),'Wrong data type'
        self.pix.append(pdt.pixel)
        self.count.append(self.count[-1]+len(pdt))
        self.xyg.extend(pdt.xyg)
        self.lam.extend(pdt.lam)
        self.val.extend(pdt.val)


    def writeH5(self,grp):
        dset=self.writeData(grp,self.xyg,self.lam,self.val,\
                            wavelengths=self.wav,pixels=self.pix,\
                            count=self.count)
        return dset
        
    def readH5(self,grp):
        try:
            data,pix,wav,cnt=self.loadData(grp,attrs=['pixels','wavelengths','count'])
            self.pix=[tuple(p) for p in pix]
            del pix

            self.count=cnt
            del cnt
            
            self.wav=columns.WAV(wav)
            del wav
            
            self.xyg=columns.XYG(data['xyg'])
            self.lam=columns.LAM(data['lam'])
            self.val=columns.VAL(data['val'])

        except:
            print("{} ODT not found".format(self.name))
        

    @property
    def npix(self):
        return len(self.pix)
    
    @property
    def nwav(self):
        return len(self.wav)

    
    def decimate(self):
        ddt=DDT(self.segid)     # create empy DDT for output
        if len(self) != 0:

        
            
            # make a one-d index
            #xyl=self.xyg.astype(dtype)+self.npix*self.lam.astype(dtype)
            xyl=self.DTYPE(self.nwav)*self.xyg.astype(self.DTYPE)+\
                 self.lam.astype(self.DTYPE)

            # find unique indices & compress
            xylu=np.unique(xyl)
            xylc=np.digitize(xyl,xylu)-1
            del xyl                # just save on memory usage


            
                        
            # sum over repeated indices
            vald=np.bincount(xylc,weights=self.val.to_numpy)
            del xylc               # just save on memory usage
            
            # go back to 2d indices
            #xygu,lamu=divmod(xylu,self.npix)
            xygu,lamu=divmod(xylu,self.nwav)
            del xylu               # just save on memory usage
            
            # get the wavelengths
            wav=self.wav.to_numpy[lamu]
            del lamu               # just save on memory usage
            
            # update the output table            
            ddt.extend(xygu,wav,vald)

        return ddt

    def __str__(self):
        return 'ODT for {}\n{} pixels and {} wavelengths'.format(self.name,self.npix,self.nwav)
        
    def __getitem__(self,pix):
        if pix in self:
            i=self.pix.index(pix)
            i0,i1=self.count[i],self.count[i+1]

            pdt=PDT(x=pix[0],y=pix[1])
            
            pdt.extend(self.xyg[i0:i1],self.lam[i0:i1],self.val[i0:i1])
            return pdt
        else:
            return None

    def __contains__(self,pix):
        return pix in self.pix
        
    def __len__(self):
        return self.count[-1]
        
    @property
    def name(self):
        return '{}'.format(self.segid)


    
if __name__=='__main__':
    wav=np.array([7000,7100,7200,7300,7400,7500,7600],dtype=np.float)
    segid=1
    o=ODT(segid,wav=wav)


    pix=(1,2)
    x=PDT(pix)
    x.extend([1,2,3,4],[2,3,4,5],[1.,2.,3.,0.5])
#    o.extend(x)

    '''
    x=PDT((2,3))
    x.extend([11,21,31,4],[0,2,4,5],[11.,21.,31.,0.5])
    o.extend(x)

    x=PDT((4,5))
    x.extend([3,4,5,4],[1,2,3,5],[0.1,0.2,0.3,0.4])
    o.extend(x)
    '''


    with h5py.File('tester.h5','w') as h5:
        x.writeH5(h5)

    with h5py.File('tester.h5','r') as h5:
        x2=PDT(pix)
        x2.readH5(h5)

