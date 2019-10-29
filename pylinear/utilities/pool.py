import multiprocessing as mp
import tqdm
import psutil as ps


from . import progressbar



class Pool(object):
    def __init__(self,ncpu=None):
        # get some settings for the processing
        ncpus=ps.cpu_count(logical=False)
        ncores=ps.cpu_count(logical=True)
        nmax=ncores-1
        
        # set a default to the max
        if ncpu is None:
            self.ncpu=nmax
        else:
            self.ncpu=min(max(ncpu,1),nmax)    # force this to be in range

    def callback(self,retval):
        #self.pb.increment()
        self.pb.update()
        
    def __call__(self,func,lis,*args,**kwargs):
        #self.pb=progressbar.ProgressBar(len(lis),**kwargs)
        if 'prefix' in kwargs:
            self.pb=tqdm.tqdm(total=len(lis),desc=kwargs['prefix'])
        else:
            self.pb=tqdm.tqdm(total=len(lis))
        if self.ncpu==1:
            print('[info]Serial processing')
            out=[]
            for l in lis:
                out.append(func(l,*args))
                #self.pb.increment()
                self.pb.update()
        else:
            print('[info]Parallel processing')



            pool=mp.Pool(processes=self.ncpu)
            results=[pool.apply_async(func,(l,*args),callback=self.callback) \
                     for l in lis]
            
            
            pool.close()
            pool.join()

            out=[]
            for result in results:
                val=result.get()
                if result.successful():
                    out.append(val)
                else:
                    print("[warn]Process failed:")
                    print('[warn]'+val)

        return out


def test(itr):
    return itr


if __name__=='__main__':
    p=Pool(ncpu=2)

    iters=[i for i in range(100)]
    iters=['hi',1,2,3,4]
    p(test,iters)
