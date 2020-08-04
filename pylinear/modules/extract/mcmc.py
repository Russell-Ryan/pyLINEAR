import emcee
import numpy as np

from ...utilities import pool


class MCMC(object):
    def __init__(self,burnfrac=0.1,nstep=100,nwalker=10):
        self.burnfrac=burnfrac
        self.nstep=nstep
        self.nwalker=nwalker
        self.pool=pool.Pool(self.__start_mcmc__,desc='Running MCMC')
        self.sampler='affine-invariant'        # DO NOT CHANGE THIS
        self._executed=False
        
    @property
    def nsample(self):
        return self.nstep*self.nwalker

    @staticmethod
    def lnlike(xj,A,bi):
        res=bi-A.matvec(xj)
        lnl=-0.5*np.sum(res*res)
        return lnl

        
    def sample(self,A,bi,sig):
        if A is None or bi is None:
            return None,None,None
        
        ndim=1
        p0=[sig*2.*np.random.randn(ndim) for _ in range(self.nwalker)]
        
        sampler=emcee.EnsembleSampler(self.nwalker,ndim,self.lnlike,
                                      args=(A,bi))
        nburn=int(self.burnfrac*self.nstep)
        sampler.run_mcmc(p0,self.nstep+nburn)


        samples=sampler.chain[:,nburn:,:].reshape((-1,1))

        ss=np.std(samples,axis=0)
        ll=np.percentile(samples,31.7,axis=0)
        aa=np.percentile(samples,50.0,axis=0)
        hh=np.percentile(samples,68.3,axis=0)

        lo=aa[0]-ll[0]
        hi=hh[0]-aa[0]
        sig=ss[0]
        
        return lo,hi,sig

    def __start_mcmc__(self,data,matrix,resid):
        j,sig=data[0],data[1]
        A,bi=matrix.sub_matrix(j,resid)
        lo,hi,rms=self.sample(A,bi,sig)
        return lo,hi,rms
  
        
    def run(self,matrix,result):
        print('[info]Computing MCMC uncertainties')
        self._executed=True

        
        # variables to iterate on
        iters=[(j,sig) for j,sig in enumerate(result.lo)]

        # compute the residuals
        resid=matrix.bi-matrix.A.matvec(result.x)

        # run the Pool
        unc=self.pool(iters,matrix,resid)
        #unc=[self.__start_mcmc__(itr,matrix,resid) for itr in iters]
        unc=list(zip(*unc))

        
        # update the results
        result.lo=np.array(unc[0])
        result.hi=np.array(unc[1])

        # return the RMS uncertainty
        return unc[2]


    def update_header(self,hdr):

        *_,last=hdr.keys()
        
        hdr.set('MCMC',value=self._executed,after=last,
                comment='was MCMC simulation performed')
        hdr.set('SAMPLER',value=self.sampler,after='MCMC',
                comment='MCMC sampler used')
        hdr.set('NWALKER',value=self.nwalker,after='SAMPLER',
                comment='number of walkers')
        hdr.set('NSTEP',value=self.nstep,after='NWALKER',
                comment='number of steps per walker')
        hdr.set('NSAMPLE',value=self.nsample,after='NSTEP',
                comment='number of samples from posterior')
        hdr.set('BURNFRAC',value=self.burnfrac,after='NSAMPLE',
                comment='fraction of steps to burn')            
        hdr.set('',value='',before='MCMC')
        hdr.set('',value='      / MCMC Settings',before='MCMC')
        hdr.set('',value='',before='MCMC')
