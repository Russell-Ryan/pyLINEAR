import h5py
import numpy as np

#class H5Utils(object):
#    def __init__(self):
#        pass





def writeGroup(h5,name,**kwargs):
    grp=h5.create_group(name)
    for k,v in kwargs.items():
        writeAttr(grp,k,v)
        
    return grp

    
def writeData(grp,name,*args,**kwargs):
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
    dset=grp.create_dataset(name,data=data)

    # these are the columns
    for arg in args:
        writeAttr(dset,arg.name,arg.description)

    # update optional keywords
    for k,v in kwargs.items():
        writeAttr(dset,k,v)


    return dset
    
def loadData(h5,name,ptype=None,attrs=None):
    dset=h5[name]
            
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
                d=loadAttr(dset,attr)
                out.append(d)
        out=tuple(out)
    else:
        out=out[0]
            
    return out
    

def writeAttr(h5,key,val):
    
    if val is not None:
        if isinstance(val,(bool,str)):
            h5.attrs[key]=np.string_(val)
        else:
            h5.attrs[key]=val

            
def loadAttr(h5,key,ptype=None):
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
    
