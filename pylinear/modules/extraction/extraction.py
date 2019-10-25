import datetime
from astropy.io import fits
import numpy as np
from shapely.geometry import Polygon
import h5py
import os,getpass
from matplotlib.backends.backend_pdf import PdfPages

import h5axeconfig

from pylinear import grism,h5table
from pylinear.utilities import gzip,indices
from . import methods,residuals,mcmcunc
from .matrix import Matrix
from . import group
from ..tabulation import tabulate
from .fluxunit import FLUXUNIT,FLUXSCALE



def getInitialGuess(mat,sources,grisms,extconf,conf):
    print('[info]Getting initial guesses')

    x0=np.zeros(mat.shape[1])
    segids=mat.segids

    for j,(segid,src) in enumerate(sources):
        try:
            index=segids.index(segid)
        except ValueError:
            index=None
            print("[warn]{} will not be extracted.".format(segid))
            
        if index is not None:
            s,g1=mat.ri[index]
            if s ==segid:
                g2=mat.lam[g1]
                init=conf['initialize'].lower()
                if init=='direct':
                    w,f,unc=src.directExtraction(grisms,extconf,conf)
                    src.sed.flam=f
                    src.sed.lamb=w
                elif init=='broadband':
                    pass
                else:
                    raise NotImplementedError("no valid initialization scheme")
                    
                x0[g1]=src.sed.interpolate(src.waves[g2])/FLUXSCALE
                
            else:
                raise IndexError("error in building initial guess")

    return x0
    
def extractSources(conf,sources,grisms,extconf,mskconf,grismFF,grpid,\
                   h5g,h5s,pdf):

    # build the matrix and check validity
    mat=Matrix(conf,grisms,sources,extconf,mskconf,grismFF)
    if not hasattr(mat,'A'):
        print("[warn]Invalid matrix.  Ignoring grpid: {}.".format(grpid))
        return
        
    # get initial guess
    x0=getInitialGuess(mat,sources,grisms,extconf,conf)
        
    # type of extraction
    method=conf['mode'].lower()
    if method == 'grid':
        result=methods.gridSearch(conf['logdamp'],mat,x0)
    elif method == 'golden':
        result=methods.goldenSearch(conf['logdamp'],mat,x0)
    elif method == 'fixed':
        result=methods.fixedDamping(conf['logdamp'],mat,x0)
    else:
        raise NotImplementedError("Extraction mode is invalid.")

    # plot
    mat.lcurve.plot(pdf,grpid=grpid)

    # write the group data
    logr1,logx,logl=mat.lcurve.values()
    c=mat.lcurve.curvature
    dtype=[('logdamp',np.float32),('logr1norm',np.float32),\
           ('logxnorm',np.float32),('curv',np.float32)]
    data=np.array(list(zip(logl,logr1,logx,c)),dtype=dtype)
    dgrp=h5g.create_dataset(str(grpid),data=data,compression='gzip')
    dgrp.attrs['istop']=np.uint8(result.istop)
    dgrp.attrs['itn']=np.uint32(result.itn)
    dgrp.attrs['r1norm']=np.float32(result.r1norm)
    dgrp.attrs['r2norm']=np.float32(result.r2norm)
    dgrp.attrs['anorm']=np.float32(result.anorm)
    dgrp.attrs['acond']=np.float32(result.acond)
    dgrp.attrs['xnorm']=np.float32(result.xnorm)
    dgrp.attrs['arnorm']=np.float32(result.arnorm)
    dgrp.attrs['damping']=np.float32(result.damp)
    dgrp.attrs['nmatrix']=np.uint64(len(mat))
    #nmat=mat.shape[0]*mat.shape[1]
    #dgrp.attrs['density']=np.float32(len(mat))/np.float32(nmat)
    dgrp.attrs['density']=np.float32(len(mat))/np.float32(mat.count)
    dgrp.attrs['time']=np.float32(result.time)
    dgrp.attrs['nsrc']=np.uint16(len(sources))
    dgrp.attrs['npix']=np.uint32(mat.shape[0])
    dgrp.attrs['nlam']=np.uint32(mat.shape[1])
    dgrp.attrs['frob']=np.float32(mat.norm)
    dgrp.attrs['ngrism']=np.uint16(len(grisms))
    
    # update with MCMC uncertainties
    result=mcmcunc.mcmcUncertainties(conf['mcmcunc'],mat,result)
    
    # package the outputs
    mcmcconf=conf['mcmcunc']       # something for easier access later  
    dtype=[('lam',np.float32),('flam',np.float32),\
           ('flo',np.float32),('fhi',np.float32)]
    for segid,src in sources:
        lam=src.waves
        flam=np.full_like(lam,np.nan)
        flo=np.full_like(lam,np.nan)
        fhi=np.full_like(lam,np.nan)
        
        
        if segid in mat.segids:
            index=mat.segids.index(segid)
            s,g1=mat.ri[index]
            if (s==segid) and (len(g1)!=0):
                g2=mat.lam[g1]
                flam[g2]=result.x[g1]
                flo[g2]=result.lo[g1]
                fhi[g2]=result.hi[g1]
        data=np.array(list(zip(lam,flam,flo,fhi)),dtype=dtype)
        dset=h5s.create_dataset(str(segid),data=data,compression='gzip')

        dset.attrs['group']=np.uint16(grpid)
        dset.attrs['RA']=np.float64(src.adc[0])
        dset.attrs['Dec']=np.float64(src.adc[1])
        dset.attrs['x']=np.float32(src.xyc[0]-src.ltv[0])
        dset.attrs['y']=np.float32(src.xyc[1]-src.ltv[1])
        dset.attrs['npix']=np.uint32(src.npix)
        dset.attrs['area']=np.float32(src.area)
        dset.attrs['total']=np.float32(src.total)
        dset.attrs['mag']=np.float32(src.mag)
        dset.attrs['lamb0']=np.float32(src.lamb0)
        dset.attrs['lamb1']=np.float32(src.lamb1)
        dset.attrs['dlamb']=np.float32(src.dlamb)
        dset.attrs['nlamb']=np.uint16(len(lam))
        dset.attrs['MCMCUNC']=np.bool(mcmcconf['perform'])
        if mcmcconf['perform']:
            dset.attrs['nwalkers']=np.uint16(mcmcconf['nwalkers'])
            dset.attrs['nstep']=np.uint32(mcmcconf['nstep'])
            dset.attrs['burn']=np.float32(mcmcconf['burn'])


    # update the residuals
    residuals.update(conf['residuals'],grisms,extconf,mat,result)
        
            

def h5yaml(h5,conf):
    for k,v in conf.items():
        if isinstance(v,dict):
            h5g=h5.create_group(k)
            h5yaml(h5g,v)
        elif isinstance(v,str):
            h5.attrs[k]=np.string_(v)
        elif v is None:
            h5.attrs[k]=np.string_("")
        else:
            h5.attrs[k]=v
            

def extract(conf,sources):
    if not conf['perform']:
        return
    
    # just some stuff for short-hand
    calconf=conf['calib']
    conffile=calconf['h5conf']

    # read grism images
    grisms=grism.Data(conf['imglst'],'img',conffile)
    
    # get the grism config data
    extconf=h5axeconfig.Camera(conffile,grisms.grism,beams=conf['beam'])
    mskconf=h5axeconfig.Camera(conffile,grisms.grism,beams=conf['mask'])
    grismFF=h5axeconfig.FlatField(calconf['h5flat'],grisms.grism)

    # set extraction values for each source
    sources.setExtractionParameters(conf,extconf)
    
    # make the tables, if need-be
    tabulate(conf['tables'],grisms,sources,extconf,'odt')
    tabulate(conf['tables'],grisms,sources,mskconf,'omt')

    # make beam masks
    path=conf['tables']['path']
    for fltname,flt in grisms:
        with h5table.H5Table(flt.dataset,'omt',path=path) as h5:
        
            for detname,detconf in mskconf:
                h5det=h5[detname]
                maskXYG=set()
                for beamname,beamconf in detconf:
                    h5beam=h5det[beamname]
                    for segid,src in sources:
                        omt=h5table.OMT(segid)
                        omt.readH5(h5beam)
                        if len(omt) != 0:
                            thisXYG=set(omt.xyg)
                            maskXYG=maskXYG.union(thisXYG)
                maskXYG=np.array(list(maskXYG),dtype=np.uint32)
                grisms[fltname][detname].extendBPX(maskXYG)


    
    
    #print('\n\n')
    #print('[debug]make beam masks here!')
    #print('\n\n')
            
    # output file names
    h5file='{}.h5'.format(conf['outroot'])
    pdffile='{}.pdf'.format(conf['outroot'])
    
    with h5py.File(h5file,'w') as h5,PdfPages(pdffile) as pdf:
        
        # set some things in the PDF
        d=pdf.infodict()
        d['Title']='L-Curve Results'
        d['Author']=getpass.getuser()
        d['Subject']='L-Curve results for grouped data from pyLINEAR.'
        d['Keywords']='pylinear grism l-curve groups'
        d['Producer']=__name__

        # update the hdf5 output
        now=datetime.datetime.now()
        h5.attrs['date']=np.string_(now.strftime("%Y-%m-%d"))
        h5.attrs['time']=np.string_(now.strftime("%H:%M:%S"))
        h5.attrs['nimage']=np.uint16(len(grisms))
        h5.attrs['nsource']=np.uint16(len(sources))
        h5.attrs['grism']=np.string_(grisms.grism)
        h5.attrs['fluxscale']=np.float32(FLUXSCALE)
        h5.attrs['fluxunit']=np.string_(FLUXUNIT)
        h5.attrs['confpath']=np.string_(os.path.abspath(conf.conffile))
        h5.attrs['conffile']=np.string_(os.path.basename(conf.conffile))

        # copy in the config
        h5y=h5.create_group("CONFIG")
        h5yaml(h5y,conf)

        # create groups for the data
        h5g=h5.create_group('GROUPS')
        h5s=h5.create_group('SPECTRA')
        h5s.attrs['nsource']=np.uint32(len(sources))


        # create dummy files for the residuals
        residuals.create(conf['residuals'],grisms,extconf)
        
        
        # extract the sources based on a grouping choice
        if conf['group']:
            # do the grouping!
            groups=group.makeGroups(conf,grisms,sources,extconf)
            ngrp=len(groups)
            for grpid,grp in enumerate(groups):
                theseSources=sources.select(grp)
                extractSources(conf,theseSources,grisms,extconf,mskconf,\
                               grismFF,grpid,h5g,h5s,pdf)
        else:
            grpid=0
            ngrp=1
            extractSources(conf,sources,grisms,extconf,mskconf,grismFF,\
                           grpid,h5g,h5s,pdf)

        # put in some data for the groups
        h5g.attrs['ngroup']=np.uint16(ngrp)


    # gzip the residuals
    residuals.gzip(conf['residuals'],grisms)
    
