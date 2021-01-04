import h5py
import numpy as np
from skimage import measure


from ..constants import COMPARGS

class H5TableBase(object):
    def __init__(self):
        pass
        
            
    def __str__(self):
        return '{} for {}'.format(self.table_type,self.name)

    def not_found(self):
        pass


    def region(self,edit=False,move=False,rotate=False,fixed=True,width=2,
               family='helvetica',size=12,bold=True,roman=True,beam='0'):

        beam=self.beam if hasattr(self,'beam') else beam
        
        mask='-' if hasattr(self,"MASK") and self.MASK else ''
        color={'0':'white','+1':'#1f77b4','+2':'#ff7f0e','+3':'#2ca02c',
              '+4':'#d62728','+5':'#9467bd','+6':'#8c564b','+7':'#e377c2',
              '+8':'#7f7f7f','+9':'#bcbd22','+10':'#17becf','-1':'#aec7e8',
              '-2':'#ffbb78','-3':'#98df8a','-4':'#ff9896','-5':'#c5b0d5',
              '-6':'#c49c94','-7':'#f7b6d2','-8':'#c7c7c7','-9':'#dbdb8d',
              '-10':'#9edae5'}.get(beam,'green')

        
        if family not in ('helvetica','times','courier'):
            family='helvetica'
        font='{family} {size}'.format(family=family,size=int(size))
        if bold:
            font+=' bold'
        if not roman:
            font+=' italic'

        x,y=self.x.to_numpy(),self.y.to_numpy()
        # get a bounding box
        x0,x1=np.amin(x)-1,np.amax(x)+1
        y0,y1=np.amin(y)-1,np.amax(y)+1

        # make a binary image
        shape=(y1-y0+1,x1-x0+1)
        img=np.zeros(shape,dtype=float)        
        img[y-y0,x-x0]=1

        # contour the image
        contours = measure.find_contours(img,level=0.5)

        # reset the contours
        cy=contours[0][:,0]+y0
        cx=contours[0][:,1]+x0
        
        coord=','.join('{},{}'.format(*xy) for xy in zip(cx,cy))
            

        region='{mask}polygon({coord}) # color={color} text={{{text}}} edit={edit} move={move} rotate={rotate} width={width} fixed={fixed} font="{font}"'.format(coord=coord,mask=mask,color=color,edit=int(edit),move=int(move),rotate=int(rotate),width=int(width),fixed=int(fixed),font=font,text=self.segid)
        return region


    
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

        # try this for overwriting data in an h5
        if name in h5:
            del h5[name]
        hd=h5.create_dataset(name,data=np.array(data,dtype=dtype),**COMPARGS)
            

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
        if name not in h5:
            return None
            
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
    
