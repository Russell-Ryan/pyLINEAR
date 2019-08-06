import os
import numpy as np
from astropy.io import fits
import datetime


import h5axeconfig
from pylinear.__init__ import __version__
from pylinear.utilities import asciitable,indices,gzip,pool
from pylinear.synthphot import SED
from pylinear import grism,h5table
from ..tabulation import tabulate

# output image data types eventually put this in the HDF5 files,
# but would require use of eval()
SCITYPE=np.float64
UNCTYPE=np.float32
DQATYPE=np.int16
TTYPE='ddt'


def addNoise(conf,sci):
    if conf['perform']:
        print("[alarm]hardcoded dark and read for WFC3/IR")
        
        dark,read=0.046,12.
        
        # create variance
        rdvar=read*read
        print(np.amax(sci))
        var=(sci+conf['skyrate']+dark)*conf['exptime']+rdvar

        # draw Poisson variables
        sci=(np.random.poisson(var)-rdvar)/conf['exptime']-conf['skyrate']-dark
        unc=np.sqrt(var)/conf['exptime']

        # force types
        sci=sci.astype(SCITYPE)
        unc=unc.astype(UNCTYPE)

    else:
        unc=np.full_like(sci,1.,dtype=UNCTYPE)

    return sci,unc



def simulateWorker(flt,conf,grismconf,grismflat,sources,overwrite=True):
    ''' helper function to facilitate multiprocessing '''

    
    path=conf['tables']['path']
    
    # make the output fits file
    hdul=fits.HDUList()

    # get the primary header from the FLT
    #hdr=flt.phdu
    hdr=fits.Header()
    
    # make a timestamp
    now=datetime.datetime.now()
          
    # update the PHDU for the output image
    hdr.append(('ORIGIN','pyLINEAR','how the file was created'),end=True)
    hdr.append(('VERSION',__version__,'pyLINEAR version'),end=True)
    hdr.append(('DATE',now.strftime("%Y-%m-%d"),\
                'date this file was written (yyyy-mm-dd)'),end=True)

    hdr.add_blank(value='',after='DATE')
    hdr.add_blank(value='/ Observational Properties')
    hdr.add_blank(value='')
    hdr.append(('TELESCOP',grismconf.telescope,\
                'telescope used to "acquire" data'),end=True)
    hdr.append(('INSTRUME',grismconf.camera,\
                'instrument used to "acquire" data'),end=True)
    hdr.append(('DETECTOR',grismconf.instrument,'detector in use'),end=True)
    hdr.append(('ROOTNAME',flt.dataset,'rootname of the observation set'),\
               end=True)
    hdr.append(('OBSTYPE','SPECTROSCOPIC',\
                'observation type - imaging or spectroscopic'),end=True)
    hdr.append(('FILTER',grismconf.grism,\
                'element selected from filter wheel'),end=True)

    hdr.add_blank(value='',after='FILTER')
    hdr.add_blank(value='/ Simulation Properties')
    hdr.add_blank(value='')
    hdr.append(('NSOURCE',len(sources),'number of simulated sources'),end=True)
    hdr.append(('SEGMAP',sources.segmap,'segmentation map'),end=True)
    hdr.append(('DETIMG',sources.obsdata.detImage,'detection image'),end=True)
    
    hdr.add_blank(value='',after='DETIMG')
    hdr.add_blank(value='/ Noise Properties')
    hdr.add_blank(value='')
    hdr.append(('NOISE',conf['noise']['perform'],'is noise added?'),end=True)
    if conf['noise']['perform']:
        hdr.append(('SKYRATE',conf['noise']['skyrate'],\
                    'sky count rate [e-/s]'),end=True)
        hdr.append(('EXPTIME',conf['noise']['exptime'],\
                    'exposure time [s]'),end=True)
        after='EXPTIME'
    else:
        after='NOISE'
        
    hdr.add_blank(value='',after=after)
    hdr.add_blank(value='/ YAML Input')
    hdr.add_blank(value='')
    hdr.add_blank(value='')
    
    for value in conf:
        hdr.add_comment(value=value)

        
    # put this in the FITS FILE    
    hdul.append(fits.PrimaryHDU(header=hdr))

    # open the H5table
    with h5table.H5Table(flt.dataset,path=path,suffix=TTYPE) as h5:
        # loop over detectors within an FLT
        for detname,det in flt:

            detgrp=h5[detname]

            detconf=grismconf[detname]

            # get the EXTVER, which describes which detector this is
            extver=detconf.extver
        
            # create an empty array
            sci=np.zeros(np.flip(det.naxis,0),dtype=SCITYPE)

            for beam,beamconf in detconf:
                beamgrp=detgrp[beam]

                
                for segid,src in sources:
                    if TTYPE=='odt':
                        odt=h5table.ODT(segid)
                        odt.readH5(beamgrp)
                        ddt=odt.decimate()
                        del odt
                    elif TTYPE=='ddt':
                        ddt=h5table.DDT(segid)
                        ddt.readH5(beamgrp)
                    else:
                        raise NotImplementedError("Invalid TTYPE")
                        
                    if len(ddt)!=0:
                        

                        # compute the (x,y) pair for each val in the DDT
                        xg,yg=indices.one2two(ddt.xyg,det.naxis)

                        # get scaling terms
                        s=beamconf.sensitivity(ddt.wav)
                        f=src.sed.interpolate(ddt.wav)
                        p=det.pixelArea(xg,yg)
                        ff=grismflat(xg,yg,ddt.wav,detname)
                        
                        # scale the DDT
                        ddt*=(s*f*p*ff)
                        del s,f,p,ff
                        
                        # sum over pixels
                        val,xyu=indices.decimate(ddt.xyg,ddt.val)
                        del ddt
                        
                        # get unique coordinates
                        xg,yg=indices.one2two(xyu,det.naxis)
                        del xyu

                        # put flux in the image
                        sci[yg,xg]+=val
                        del val
                        

            sci,unc=addNoise(conf['noise'],sci)
            
            # create a DQA image
            dqa=np.full_like(sci,0,dtype=DQATYPE)
            
            # the SCI image
            hdr=det.mkhdr(SCITYPE,extname=detconf.sciext,extver=extver)
            hdul.append(fits.ImageHDU(data=sci,header=hdr))
            
            # the UNC image
            hdr=det.mkhdr(UNCTYPE,extname=detconf.uncext,extver=extver)
            hdul.append(fits.ImageHDU(data=unc,header=hdr))
            
            # the DQA image
            hdr=det.mkhdr(DQATYPE,extname=detconf.dqaext,extver=extver)
            hdul.append(fits.ImageHDU(data=dqa,header=hdr))


        

        
    # output the file
    outfile=flt.filename
    print('writing simulated image {}'.format(outfile))
    hdul.writeto(outfile,overwrite=overwrite)

    # do we gzip?
    if conf['gzip']:
        gzip.gzip(outfile)
        outfile+='.gz'

    return outfile            
        


def simulate(conf,sources):
    if not conf['perform']:
        return
    print("[info]Simulating FLTs")

    # get the grism config data
    grismconf=h5axeconfig.Camera(conf['calib']['h5conf'],conf['grism'],\
                                 beams=conf['beam'])
    grismflat=h5axeconfig.FlatField(conf['calib']['h5flat'],conf['grism'])
    
    # read grisms
    grisms=grism.Data(conf['imglst'],conf['imgtype'],conf['calib']['h5siaf'])
                      
    # make the tables
    tabulate(conf['tables'],grisms,sources,grismconf,'odt')

            
    # get detection stuff (just for shorthand)
    detband=sources.obsdata.detBandpass

    # set the spectrum to each source
    table=asciitable.AsciiTable(['segid','file','z'],filename=conf['sedlst'])
    for segid,sedfile,z in table:
        if segid in sources:
            # read the SED
            sed=SED(filename=sedfile)

            # apply the redshift
            sed.redshift(z)

            # get expect flux from the detection image
            modflam=sources[segid].total*detband.photflam

            # compute the flux in the SED through the filter
            aveflam=detband.aveflux(sed,flam=True)
            
            # rescale the spectrum
            sed*=(modflam/aveflam)

            # reset the spectrum
            sources[segid].sed=sed
    
    # the things that do not change
    args=(conf,grismconf,grismflat,sources)
    
    # use my version of pool to codify the use of this
    pool.pool(simulateWorker,grisms.values(),*args,ncpu=conf['cpu']['ncpu'])
