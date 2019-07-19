import datetime
from astropy.io import fits
import numpy as np

import h5axeconfig

from pylinear import grism
from pylinear.utilities import gzip
from . import methods,residuals,mcmcunc
from .matrix import Matrix
from ..tabulation import tabulate
from .fluxunit import FLUXUNIT



def getInitialGuess(mat,sources):
    print('Getting initial guesses')

    x0=np.zeros(mat.shape[1])
    segids=mat.segids

    for j,(segid,src) in enumerate(sources):
        try:
            index=segids.index(segid)
        except ValueError:
            index=None
            print("{} will not be extracted.".format(segid))

            
        if index is not None:
            s,g1=mat.ri[index]
            if s ==segid:
                g2=mat.lam[g1]
                x0[g1]=src.sed.interpolate(src.waves[g2])/FLUXUNIT
            else:
                raise IndexError("error in building initial guess")

    return x0
    




def writeFITS(conf,result,mat,sources,method):
    print("writing output fits file")
    
    # make a timestamp
    now=datetime.datetime.now()
  
    # create the fits output
    hdul=fits.HDUList()

    # add primary extension
    hdr=fits.Header()
    hdr.append(('DATE',now.strftime("%Y-%m-%d"),\
                'date this file was written (yyyy-mm-dd)'),end=True)
    hdr.add_blank(value='',after='DATE')
    hdr.add_blank(value='/ Input Properties')
    hdr.add_blank(value='')
    
    hdr.append(('NSOURCES',mat.nsrc,'Number of sources'),end=True)
    hdr.append(('NIMAGES',mat.nimg,'Number of grism images'),end=True)
    hdr.append(('NPIXELS',mat.shape[0],\
                'Number of knowns (extracted pixels'),end=True)               
    hdr.append(('NLAMB',mat.shape[1],\
                'Number of unknowns (inferred wavelengths'),end=True)
    hdr.append(('FLUXUNIT',FLUXUNIT,'erg/s/cm2/A'),end=True)
    hdr.append(('FROBNORM',mat.frob,'Frobenius norm of A'),end=True)
    
    hdr.add_blank(value='',after='FROBNORM')
    hdr.add_blank(value='/ LSQR Settings')
    hdr.add_blank(value='')
    
    hdr.append(('DAMPING',result.damp,'Unscaled damping parameter'),end=True)
    hdr.append(('ISTOP',result.istop,'Stopping condition'),end=True)
    hdr.append(('ITER',result.iters,'Number of iterations'),end=True)
    hdr.append(('ATOL',mat.atol,'Stopping criterion'),end=True)
    hdr.append(('BTOL',mat.btol,'Stopping criterion'),end=True)
    hdr.append(('CONLIM',mat.conlim,'Stopping criterion'),end=True)
    hdr.append(('R1NORM',result.r1norm,\
                'norm(r) with r=b-Ax, like sqrt(chi2)'),end=True)
    hdr.append(('R2NORM',result.r2norm,\
                'sqrt(norm(r)^2+damp^2*norm(x)^2)'),end=True)
    hdr.append(('ANORM',result.anorm,\
                'Frobenius norm of A=[[A];[damp*I]]'),end=True)
    hdr.append(('ACOND',result.acond,'Condition of A'),end=True)
    hdr.append(('ARNORM',result.arnorm,'norm(A^T*r-damp^2*x)'),end=True)
    hdr.append(('XNORM',result.xnorm,'norm(x)'),end=True)
    hdr.append(('LSQRTIME',result.time,'Runtime for LSQR in sec'),end=True)
    hdr.append(('METHOD',method,'Method for running'),end=True)
    
    hdr.add_blank(value='',after='METHOD')
    hdr.add_blank(value='/ YAML Input')
    hdr.add_blank(value='')
    for value in conf:
        hdr.add_comment(value=value)

    hdul.append(fits.PrimaryHDU(header=hdr))
    # ------------------------------------------------------------------------


    # now create extensions for each source
    dtype=np.float32           # output data type
    segids=mat.segids
    unit='{} erg/s/cm2/A'.format(FLUXUNIT)
    for segid,src in sources:
        # make output arrays
        lam=src.waves.astype(dtype)
        flm=np.full_like(lam,np.nan,dtype=dtype)
        flo=np.full_like(lam,np.nan,dtype=dtype)
        fhi=np.full_like(lam,np.nan,dtype=dtype)

        # test if object was extracted
        if segid in segids:
            index=segids.index(segid)
            s,g1=mat.ri[index]
            if s==segid and len(g1)!=0:
                g2=mat.lam[g1]

                flm[g2]=result.x[g1]
                flo[g2]=result.lo[g1]
                fhi[g2]=result.hi[g1]

        # create the columns
        col1=fits.Column(name='lamb',format='E',array=lam,unit='A')
        col2=fits.Column(name='flam',format='E',array=flm,unit=unit)
        col3=fits.Column(name='lounc',format='E',array=flo,unit=unit)
        col4=fits.Column(name='hiunc',format='E',array=fhi,unit=unit)
        hdu=fits.BinTableHDU.from_columns([col1,col2,col3,col4])
        
        # add some data to the header
        hdu.header.append(('EXTNAME',str(segid),'Extension name'),end=True)
        #hdu.header.append(('EXTNAME','SED','Extension name'),end=True)
        #hdu.header.append(('EXTVER',segid,'Extension version'),end=True)
        hdu.header.add_blank(value='')
        hdu.header.add_blank(value='/ Source Properties')
        hdu.header.add_blank(value='')
        hdu.header.append(('SEGID',segid,'Segmentation ID'),end=True)
        hdu.header.append(('RA0',src.adc[0],'RA center of mass'),end=True)
        hdu.header.append(('DEC0',src.adc[1],'Dec center of mass'),end=True)
        hdu.header.append(('NPIX',src.npix,'Number of pixels'),end=True)
        hdu.header.append(('AREA',src.area,'Area (sq. arcsec)'),end=True)
        hdu.header.append(('FLUX',src.total,'Flux in direct image units'),\
                          end=True)
        hdu.header.append(('MAG',src.mag,'Magnitude of direct image'),\
                          end=True)

        hdu.header.add_blank(value='',after='MAG')
        hdu.header.add_blank(value='/ Extraction Properties')
        hdu.header.add_blank(value='')
        hdu.header.append(('NLAMB',len(lam),'Number of wavelengths'),\
                          end=True)
        hdu.header.append(('LAMB0',src.lamb0,'Lower bound in A'),end=True)
        hdu.header.append(('LAMB1',src.lamb1,'Upper bound in A'),end=True)
        hdu.header.append(('DLAMB',src.dlamb,'Resolution in A'),end=True)
        
        hdu.header.add_blank(value='',after='DLAMB')
        hdu.header.add_blank(value='/ MCMC Settings')
        hdu.header.add_blank(value='')

        mcmcconf=conf['mcmcunc']
        hdu.header.append(('MCMCUNC',mcmcconf['perform'],\
                           'MCMC Simulation for uncertainties'),end=True)
        if mcmcconf['perform']:
            hdu.header.append(('NWALKERS',mcmcconf['nwalkers'],\
                               'Number of walkers'),end=True)
            hdu.header.append(('NSTEP',mcmcconf['nstep'],\
                               'Number of steps per walker'),end=True)
            hdu.header.append(('BURN',mcmcconf['burn'],\
                               'fraction of steps to burn'),end=True)

        hdul.append(hdu)
        

    # write to disk
    outfile='{}_spc.fits'.format(conf['outroot'])
    hdul.writeto(outfile,overwrite=True)
    gzip.gzip(outfile)


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
    grismFF=h5axeconfig.FlatField(calconf['h5flat'])

    
    # make the tables if need-be
    tabulate(conf['tables'],grisms,sources,extconf,'odt')
    #tabulate(conf['tables'],grisms,sources,mskconf,'omt')


    # set extraction values for each source
    print('move extraction parameters out of matrix.py to here')

    
    # build the matrix and guesses
    mat=Matrix(conf,grisms,sources,extconf,mskconf,grismFF)
    x0=getInitialGuess(mat,sources)

    
    # type of extraction
    method=conf['mode'].lower()
    if method == 'grid':
        result=methods.gridSearch(conf['logdamp'],mat,x0)
    elif method == 'golden':
        result=methods.goldenSearch(conf['logdamp'],mat,x0)
    elif method == 'fixed':
        result=methods.fixedDamping(conf['logdamp'],mat,x0)
    elif method == 'classic':
        result=methods.classicExtraction()
    else:
        raise NotImplementedError("Extraction mode is invalid.")
    
    # make the LCurve plot
    mat.lcurve(conf['outroot'])

    # update with MCMC uncertainties
    result=mcmcunc.mcmcUncertainties(conf['mcmcunc'],mat,result,sources)

    # compute the residuals
    residuals.computeResiduals(conf['residuals'],grisms,extconf,mat,result)

    # write to disk
    writeFITS(conf,result,mat,sources,method)

