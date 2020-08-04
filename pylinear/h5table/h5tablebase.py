import h5py
import numpy as np

class H5TableBase(object):
    def __init__(self):
        pass
            
    def __str__(self):
        return '{} for {}'.format(self.table_type,self.name)

    def not_found(self):
        pass
    
    @property
    def table_type(self):
        return self.__class__.__name__


    @staticmethod
    def write_group(h5,name,**kwargs):
        ''' write/create a group and update attributes '''

        hf=h5.require_group(name)
        for k,v in kwargs.items():
            H5TableBase.write_attribute(hf,k,v)
            
        return hf

    @staticmethod
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
        hd=h5.create_dataset(name,data=data)
            

        # these are the columns
        for arg in args:
            H5TableBase.write_attribute(hd,arg.name,arg.description)

        # update optional keywords
        for k,v in kwargs.items():
            H5TableBase.write_attribute(dset,k,v)

            
        return hd

    @staticmethod
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
                        d=H5TableBase.load_attribute(dset,attr)
                        out.append(d)
                out=tuple(out)
        else:
            out=out[0]
            
        return out

    @staticmethod
    def write_attribute(h5,key,val):
        ''' write an attribute to the hdf5 object '''
        
        if val is not None:
            if isinstance(val,(bool,str)):
                h5.attrs[key]=np.string_(val)
            else:
                h5.attrs[key]=val

    @staticmethod
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
    
