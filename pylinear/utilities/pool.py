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
        nmax=ncores-1
        
        # set a default to the max
        if ncpu is None:
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
            
    def __call__(self,itrs,*args,**kwargs):
        ''' call the pool '''

        total=len(itrs)    # number of iterations to do
        if self.ncpu==1:
            if not self.quiet:
                print('[info]Serial Processing')
            results=[self.func(i,*args,**kwargs) for i in
                     tqdm.tqdm(itrs,total=total,desc=self.desc)]
            
        else:
            if not self.quiet:
                print('[info]Parallel Processing')
            if kwargs is not None:
                func=self.func
                self.func=partial(self.func,**kwargs)
            p=mp.Pool(processes=self.ncpu)
            imap=p.imap(self.__worker__,self.__zip__(itrs,*args))
            results=list(tqdm.tqdm(imap,total=total,desc=self.desc))
            if kwargs is not None:
                self.func=func
            
        return results





##################   STUFF FOR TESTING   ##################
    
def testWorker(itr,dt,a,test=1):
    time.sleep(dt)
    return test*(itr+a)
   
    
    
if __name__=='__main__':
    import time,timeit



    
    itrs=[0,1,2,3,4,5,6,7,8,9,10,11]
    dt=0.1
    a=1
    t0=timeit.default_timer()
    p=Pool(testWorker,ncpu=2,desc='test',quiet=True)
    results=p(itrs,dt,a,test=3)
    t1=timeit.default_timer()
    print(t1-t0)
    
