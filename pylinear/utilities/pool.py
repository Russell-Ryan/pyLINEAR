import multiprocessing as mp
import psutil as ps

''' utility to call the multiprocessing '''


def pool(func,iterator,*args,ncpu=None):

    # get some settings for the processing
    ncpus=ps.cpu_count(logical=False)
    ncores=ps.cpu_count(logical=True)
    nmax=ncores-1

    
    # set a default to the max
    if ncpu is None:
        ncpu=nmax
    else:
        ncpu=min(max(ncpu,1),nmax)    # force this to be in range

        
    # start the processing
    if ncpu==1:
        print('Serial processing')
        out=[func(it,*args) for it in iterator]
    else:
        print('Parallel processing')
        pool=mp.Pool(processes=ncpu)

        results=[pool.apply_async(func,(it,*args)) for it in iterator]
        pool.close()
        pool.join()


        # out=[result.get() for result in results if result.successful()]
        out=[]
        for result in results:
            if result.successful():
                out.append(result.get())
            else:
                print("Process failed.")

    return out
    
    

if __name__=='__main__':
    pool('func','iterator')

    
    
