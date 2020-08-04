import h5py
import numpy as np


'''
   A suite of routines to facilitate reading/writing groups, data
   and attributes to HDF5 objects.  This ensures that the data is 
   passed in/out with the same numpy representation.

'''




def write_group(h5,name,**kwargs):
    ''' write/create a group and update attributes '''

    hf=h5.require_group(name)
    for k,v in kwargs.items():
        write_attribute(hf,k,v)
        
    return hf

    
def write_data(h5,name,*args,**kwargs):
    ''' write/create data and update attributes '''

    n=len(args)
    if n==0:
        return None
    elif n==1:
        data=np.array(args[0]) #np.array(list(args[0]))
        dtype=args[0].dtype #(args[0].name,args[0].dtype)
        
    else:
        data=list(zip(*args))
        dtype=[(arg.name,arg.dtype) for arg in args]

            
    data=np.array(data,dtype=dtype)            

    # try this for overwriting data in an h5
    if name in h5:
        del h5[name]
    dset=h5.create_dataset(name,data=data)


    # these are the columns
    for arg in args:
        write_attributes(dset,arg.name,arg.description)

    # update optional keywords
    for k,v in kwargs.items():
        write_attribute(dset,k,v)


    return dset
    
def load_data(h5,name,ptype=None,attrs=None):
    ''' load the data and grab the attributes '''

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
                d=load_attribute(dset,attr)
                out.append(d)
        out=tuple(out)
    else:
        out=out[0]
            
    return out
    

def write_attribute(h5,key,val):
    ''' write an attribute to the hdf5 object '''

    if val is not None:
        if isinstance(val,(bool,str)):
            h5.attrs[key]=np.string_(val)
        else:
            h5.attrs[key]=val

            
def load_attribute(h5,key,ptype=None):
    ''' load the attributes from the hdf5 object '''


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
    
