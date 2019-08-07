import emcee
import numpy as np
from astropy.io import fits
#import multiprocessing as mp

#from linear import exceptions

from pylinear.utilities import indices,pool

def mp_mcmcUncertainty(A,bi,func,conf):
    ndim=1

    p0=[]
    nwalkers=conf['nwalkers']
    for i in range(nwalkers):
        p0.append(np.array([func*2.*np.random.randn()]))
        #p0=[0.0]
    cindex=0
        
    sampler=emcee.EnsembleSampler(nwalkers,ndim,lnlike,args=(A,bi))
        
    #sampler=emcee.MHSampler(cov,ndim,lnlike,args=(A,bi))


        
    sampler.run_mcmc(p0,conf['nstep'])
    nburn=int(conf['burn']*conf['nstep'])
    samples=sampler.chain[:,nburn:,:].reshape((-1,1))
    ss=np.std(samples,axis=0)
    ll=np.percentile(samples,31.7,axis=0)
    aa=np.percentile(samples,50.0,axis=0)
    hh=np.percentile(samples,68.3,axis=0)
   
    lo=aa[0]-ll[0]
    hi=hh[0]-aa[0]
    sig=ss[0]

    return lo,hi,sig


def lnlike(x,A,bi):
    resid=bi-A.matvec(x)
    lnl=-0.5*np.sum(resid*resid)
    return lnl


def mcmcUncertainties(conf,mat,result,sources):
    if not conf['perform']:
        return result

    print('[info]Computing MCMC uncertainties')
    print('[debug]MCMC must be single processor')
    
    # compute the residuals
    resid=mat.bi-mat.A.matvec(result.x)


    # set up for the MPU

    # single processor
    lo,hi,sig=[],[],[]
    for j,func in enumerate(result.lo):
        A,bi=mat.residualMatrix(j,resid)
        l,h,s=mp_mcmcUncertainty(A,bi,func,conf)
        lo.append(l)
        hi.append(h)
        sig.append(s)
        

    # set the outputs
    result.lo=np.array(lo)
    result.hi=np.array(hi)


    return result

    
