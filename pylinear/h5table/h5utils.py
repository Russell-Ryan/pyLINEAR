import h5py
import numpy as np

class H5Utils(object):
    def __init__(self):
        pass

    def writeGroup(self,h5,**kwargs):
        grp=h5.create_group(self.name)
        for k,v in kwargs.items():
            self.writeAttr(grp,k,v)
            
        return grp

    
    def writeData(self,grp,*args,**kwargs):
        n=len(args)
        if n==0:
            return
        elif n==1:
            data=np.array(args[0]) #np.array(list(args[0]))
            dtype=args[0].dtype #(args[0].name,args[0].dtype)
        
        else:
            data=list(zip(*args))
            dtype=[(arg.name,arg.dtype) for arg in args]

            
        data=np.array(data,dtype=dtype)
            
        dset=grp.create_dataset(self.name,data=data)

        
        

        self.writeAttr(dset,'type',self.__class__.__name__)


        for arg in args:
            self.writeAttr(dset,arg.name,arg.description)

                           
        for k,v in kwargs.items():
            self.writeAttr(dset,k,v)


        return dset

    def loadData(self,h5,ptype=None,attrs=None):
        dset=h5[self.name]
        if self.loadAttr(dset,'type') != self.__class__.__name__:
            raise RuntimeError('incompatible table types')
        
        
        # make a list for the output
        out=[]
        out.append(dset[:])

        # recast if necessary
        if isinstance(ptype,type):
            out[0]=ptype(out[0])


        # read the keywords that the user asked for            
        if attrs is not None:
            for attr in attrs:
                if attr in dset.attrs:
                    d=self.loadAttr(dset,attr)
                    out.append(d)
            out=tuple(out)
        else:
            out=out[0]
            
        return out
    

    def writeAttr(self,h5,key,val):
        if val is not None:
            if isinstance(val,(bool,str)):
                h5.attrs[key]=np.string_(val)
            else:
                h5.attrs[key]=val

    def loadAttr(self,h5,key,ptype=None):
        val=h5.attrs[key]
        if isinstance(val,bytes):
            val=val.decode('UTF-8')
            vlo=val.lower()
            if vlo=='true':
                val=True
            elif vlo=='false':
                val=False
            elif vlo=='none':
                val=None
            else:
                pass
        elif isinstance(val,float):
            if np.isnan(val):
                val=None
            else:
                pass
        else:
            pass
            
        if isinstance(ptype,type):
            val=ptype(val)
            
        return val
    
