import time,timeit

import pool


def testWorker(itr,dt,a,test=1):
    time.sleep(dt)
    return test*(itr+a)
   
    
    
if __name__=='__main__':
    



    
    itrs=[0,1,2,3,4,5,6,7,8,9,10,11]
    dt=0.1
    a=1
    t0=timeit.default_timer()
    p=pool.Pool(testWorker,ncpu=2,desc='test',quiet=True)
    results=p(itrs,dt,a,test=3)
    t1=timeit.default_timer()
    print(t1-t0)
    
