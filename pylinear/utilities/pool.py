import tqdm
import multiprocessing as mp
import psutil as ps
from functools import partial


class Pool(object):
    def __init__(self,func,ncpu=None,desc=None,quiet=False):
        ''' instantiate the pool '''

        # get some settings for the processing
        ncpus=ps.cpu_count(logical=False)
        ncores=ps.cpu_count(logical=True)
        nmax=ncores-2      
        
        # set a default to the max
        if ncpu is None or ncpu<=0:
            self.ncpu=nmax
        else:
            self.ncpu=min(max(ncpu,1),nmax)    # force this to be in range
        self.desc=desc
        self.func=func
        self.quiet=quiet
            


    def __zip__(self,itrs,*args):
        ''' internal generator to zip iterables to scalars '''
        for itr in itrs:
            yield (itr,*args)
        
    def __worker__(self,args):
        ''' internal method to unpack arguments '''
        return self.func(*args)


    def __str__(self):
        lines=['Pool object with:',
               'NCPU = {}'.format(self.ncpu),
               'FUNC = {}'.format(self.func)]
        return '\n'.join(lines)
    
    def __call__(self,itrs,*args,**kwargs):
        ''' call the pool '''

        total=len(itrs)    # number of iterations to do
        if self.ncpu==1:
            print('[info]Serial Processing')
            results=[self.func(i,*args,**kwargs) for i in
                     tqdm.tqdm(itrs,total=total,desc=self.desc)]
            
        else:
            print('[info]Parallel Processing: {} processes'.format(self.ncpu))
            if kwargs is not None:
                func=self.func
                self.func=partial(self.func,**kwargs)

            with mp.Pool(processes=self.ncpu) as p:
                imap=p.imap(self.__worker__,self.__zip__(itrs,*args))
                results=list(tqdm.tqdm(imap,total=total,desc=self.desc))

                
            #p=mp.Pool(processes=self.ncpu)
            #imap=p.imap(self.__worker__,self.__zip__(itrs,*args))
            #results=list(tqdm.tqdm(imap,total=total,desc=self.desc))
                        
            if kwargs is not None:
                self.func=func
            
        return results



if __name__=='__main__':
    from time import sleep
    import numpy as np
    def func(t):
        x=np.zeros((20000,20000),dtype=np.float)
        y=np.zeros_like(x)
        z=np.zeros_like(x)
        w=np.zeros_like(x)
        sleep(t)
        return float(t)
        
    #func = lambda x: sleep(x)


    p=Pool(func,ncpu=4)
    r=p([1,2,3,4,2,3,5,3,2,4,2,1])
    print(r)


    import pdb
    pdb.set_trace()
