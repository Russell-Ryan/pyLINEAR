import h5py
import numpy as np
import os
import datetime

from . import h5utils

class H5Table(object):
    def __init__(self,dataset,suffix,path=None):
        
        # sort out some things w.r.t. the path
        if path is None:
            path=os.getcwd()
            
        if not os.path.exists(path):
            os.makedirs(path)

        # save some things
        self.dataset=dataset
        self.suffix=suffix

        # just a place holder
        self.h5=None
            

        # build the filename
        self.filename='{}_{}.h5'.format(self.dataset,self.suffix)
        self.filename=os.path.join(path,self.filename)
    

    def __enter__(self):
        self.h5=h5py.File(self.filename,'a')
        h5utils.writeAttr(self.h5,'type',self.suffix)
        now=datetime.datetime.now()
        h5utils.writeAttr(self.h5,'date',now.strftime("%Y-%m-%d"))
        h5utils.writeAttr(self.h5,'started',now.strftime("%H:%M:%S"))        

        return self.h5

    def __exit__(self,etype,eval,etrace):
        self.close()

    def __del__(self):
        self.close()


    def close(self):
        if self.h5 is not None:
            now=datetime.datetime.now()
            
            h5utils.writeAttr(self.h5,'finished',now.strftime("%H:%M:%S"))
            self.h5.close()

            self.h5=None
