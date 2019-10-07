import emcee
import numpy as np
from astropy.io import fits


from pylinear.utilities import indices,pool

def mp_mcmcUncertainty(A,bi,func,conf):
    if A is None or bi is None:
        return None,None,None
    
    ndim=1


    p0=[]
    nwalkers=conf['nwalkers']
    for i in range(nwalkers):
        p0.append(np.array([func*2.*np.random.randn()]))
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


def mcmcStart(data,mat,resid,conf):
    return mp_mcmcUncertainty(*mat.residualMatrix(data[0],resid),data[1],conf)


def mcmcUncertainties(conf,mat,result):
    if not conf['perform']:
        return result

    print('[info]Computing MCMC uncertainties')
    
    
    # compute the residuals
    resid=mat.bi-mat.A.matvec(result.x)

    # set up the iterates
    iters=[(j,f) for j,f in enumerate(result.lo)]
    
    # do the processing
    p=pool.Pool(ncpu=conf['cpu']['ncpu'])
    unc=p(mcmcStart,iters,mat,resid,conf,prefix='Running MCMC')

    # package the outputs
    unc=list(zip(*unc))
    result.lo=np.array(unc[0])
    result.hi=np.array(unc[1])
    


    return result

    
