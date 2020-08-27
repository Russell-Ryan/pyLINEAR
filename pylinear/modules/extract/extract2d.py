import numpy as np
from astropy.io import fits
from datetime import datetime
from timeit import default_timer

import os,pwd
from matplotlib.backends.backend_pdf import PdfPages

from ... import info
from ...config import Config
from .. import header_utils
from .residuals import Residuals
from .extract import Extract



def extract2d(grisms,sources,beams,logdamp,method,fileroot,path,
              inverter='lsqr',mskbeams=None):

    # record the starting time
    t1=default_timer()    
    
    # specify some filenames
    x2dfile='{}_x2d.fits'.format(fileroot)
    pdffile='{}_lcv.pdf'.format(fileroot)

    # what force beams to be a list
    if not isinstance(beams,(tuple,list)):
        beams=[beams]
        
    # fix the masking of beams
    if mskbeams is not None and not isinstance(mskbeams,(tuple,list)):
        mskbeams=[mskbeams]


    # build an extraction object
    extract=Extract(inverter=inverter,method=method)

    
    # process each group
    with PdfPages(pdffile) as pdf:
        # put some stuff in the PDF
        d=pdf.infodict()
        d['Title']='L-Curve Results'
        d['Author']=pwd.getpwuid(os.getuid()).pw_gecos  #getpass.getuser()
        d['Subject']='L-Curve results for grouped data from pyLINEAR.'
        d['Keywords']='pylinear grism l-curve groups'
        d['Producer']=__name__


        # make something for residuals
        residuals=Residuals(grisms)


        # build a matrix
        extract.load_matrix_file(grisms,sources,beams,path,group=group,
                                 mskbeams=mskbeams)
        #extract.build_matrix(grisms,sources,beams,path,mskbeams=mskbeams)

        # run extraction method
        sres,gres=extract.run(logdamp,pdf=pdf,mcmc=False,
                              residuals=residuals)

        # finalize the residuals
        residuals.apply_uncertainty()
        residuals.gzip_files()

        
    # compute the runtime
    t2=default_timer()
    dt=t2-t1
    days,rem=divmod(dt,24*60*60)
    hours,rem=divmod(rem,60*60)
    mins,secs=divmod(rem,60)
    times=(int(days),int(hours),int(mins),int(secs))

    # get a timestamp
    now=datetime.now()
    runtime='{0}d{1:02d}h{2:02d}m{3:02d}s'.format(*times)

    
    # now must unpack the sres array to make a flux cube
    print('[debug]This is hardcoded for a single-pixel region')

    # all of this is probably better in sources.composite, pass in sres
    segids=list(sres.keys())
    nwav=sources.composite.nwavelength()
    dtype=np.float64
    flam=np.full([nwav,*sources.composite.shape],np.nan,dtype=dtype)
    func=np.full([nwav,*sources.composite.shape],np.nan,dtype=dtype)
    for ss,bbox in sources.composite.items():
        x0=bbox[0]+sources.composite.ltv[0]
        x1=bbox[1]+sources.composite.ltv[0]
        y0=bbox[2]+sources.composite.ltv[1]
        y1=bbox[3]+sources.composite.ltv[1]

        flam[:,y0,x0]=sres[ss].data['flam']
        func[:,y0,x0]=sres[ss].data['flounc']

    # packge this into a fits HDU
    hdr=sources.composite.mkhdr(dtype,EXTNAME='CUBE',EXTVER=sources.cubeid,
                                CTYPE3='AWAV',CUNIT3='Angstrom',
                                CD3_3=sources.composite.dlamb,
                                CRVAL3=sources.composite.lamb0,CRPIX3=1.,
                                CD1_3=0.,CD2_3=0.,CD3_1=0.,CD3_2=0.,
                                CRDER3=0.)#,NAXIS3=nwav)
    hdr['NAXIS']=3   # update the number of axes
    hdr.set('NAXIS3',value=nwav,comment='number of wavelengths',after='NAXIS2')

    
    fhdu=fits.ImageHDU(flam,header=hdr)

    hdr['EXTNAME']='UNC'
    uhdu=fits.ImageHDU(func,header=hdr)
        

    # make a PHDU
    phdu = fits.PrimaryHDU()
    header_utils.add_software_log(phdu.header)

    *_,after=phdu.header.keys()
    
    phdu.header.set('DETFILE',value=sources.obscat.detfile,after=after,
                    comment='image for detection weights')
    phdu.header.set('NGROUP',value=1,after='DETFILE',
                    comment='number of groups')
    phdu.header.set('NGRISM',value=len(grisms),after='NGROUP',
                    comment='number of grism exposures')                    
    phdu.header.set('NSOURCE',value=len(sources),after='NGRISM',
                    comment='number of sources')
    header_utils.add_stanza(phdu.header,'Observational Settings',
                            before='DETFILE')
    
    
    # save the config
    Config().update_header(phdu.header)

    # put in the disclaimer
    header_utils.add_disclaimer(phdu.header)
    
    # oky... let's put the file together
    hdul=fits.HDUList()

    # the primary header
    hdul.append(phdu)
    hdul.append(fhdu)
    hdul.append(uhdu)
    hdul.append(gres)
    

    # write the file now...
    hdul.writeto(x2dfile,overwrite=True,output_verify='ignore')
