import os
import numpy as np
from astropy.io import fits

from .. import header_utils
from ...config import Config
from ... import h5table
from ...utilities import Pool,gzip,indices
class Simulate(object):    
    def __init__(self,sedlst,path='tables',ncpu=1,gzip=True,overwrite=True):
        self.sedlst=sedlst
        self.gzip=gzip
        self.ncpu=ncpu
        self.path=path
        self.overwrite=overwrite

    def simulate(self,grism,sources,beam,overwrite=None):
        if overwrite is None:
            overwrite=self.overwrite
            
        dataset=grism.dataset
        with h5table.H5Table(dataset,path=self.path,mode='r') as tab:
            # create the fits file
            hdul=fits.HDUList()

            # create a primary header
            phdr=fits.Header()

            # put the OBSTYPE in for all grism exposures as "SPECTROSCOPIC"
            last=header_utils.get_last_keyword(phdr)
            phdr.set('OBSTYPE',value='SPECTROSCOPIC',last=last,
                     comment='observation type - imaging or spectroscopic')

            # add the software log
            header_utils.add_software_log(phdr)

            # put a bunch of stuff in the primary header
            stanza='Observational Settings'
            grism.detector.header.update_header(phdr,stanza=stanza)
            
            # update the primary header with the settings
            Config().update_header(phdr)

            # put a comment at the end
            header_utils.add_disclaimer(phdr)
            
            # save the primary header
            hdul.append(fits.PrimaryHDU(header=phdr))

            # get the flt name
            fltname=grism.filename
            for device in grism:
                # open the tab for this grism device
                #tab.open_device(device.name)
                tab.open_table(device.name,beam,'pdt')
            
                # create an image
                naxis=(device.naxis1,device.naxis2)
                sci=np.zeros(naxis,dtype=device.exten['science'].dtype)

                # get the sensitivity curve
                beamconf=device.load_beam(beam)

                # load the flat field
                flatfield=beamconf.load_flatfield()

                # process each source
                for source in sources:
                    
                    # read the ODT
                    odt=tab.load_from_file(source,beam,'odt')

                    # decimate
                    ddt=odt.decimate(*naxis)

                    # get a few things
                    x=ddt.x.to_numpy()
                    y=ddt.y.to_numpy()
                    wav=ddt.wav.to_numpy()

                    # need to apply several things:
                    # 1. sensitivity curve
                    # 2. flat field
                    # 3. pixel area
                    # 4. spectrum of the source
                    
                    # get the sensitivity curve
                    sens=beamconf.sensitivity(wav)
                    
                    # get the flat field value
                    ff=flatfield(x,y,wav)

                    # compute the pixel area
                    area=device.pixel_area_map(x,y)

                    # compute the spectrum at some point
                    flam=source.sed.interpolate(wav)

                    # scale the value from the DDT
                    val=ddt.val.to_numpy()*sens*ff*area*flam

                    # sum over pixels in the grism image
                    xyg=x.astype(np.uint64)+naxis[0]*y.astype(np.uint64)
                    valu,xygu=indices.decimate(xyg,val)
                    xg,yg=indices.one2two(xygu,naxis)

                    # update the image
                    sci[yg,xg]+=valu


                # make the sci image to the header
                hdr=device.mkhdr(sci.dtype,imgtype='science')
                hdul.append(fits.ImageHDU(data=sci,header=hdr))

                # add sky background
                sci+=device.add_background()
                                
                # create a Uncertainty
                unc=device.make_uncertainty(sci)
                hdr=device.mkhdr(unc.dtype,imgtype='uncertainty')
                hdul.append(fits.ImageHDU(data=unc,header=hdr))

                # create a DQA image
                dqa=np.full_like(sci,0,device.exten['dataquality'].dtype)
                hdr=device.mkhdr(dqa.dtype,imgtype='dataquality')
                hdul.append(fits.ImageHDU(data=dqa,header=hdr))


            # write the file to disk
            hdul.writeto(fltname,overwrite=overwrite)
            hdul.close()


            
        # check that a file was written
        if os.path.exists(fltname):
            if self.gzip:
                # do we gzip the file?  update the filename
                gzip.gzip(fltname)
                fltname+='.gz'
        else:
            fltname=None
               
        return fltname

    def run(self,grisms,sources,beam):

        # load the SEDs
        sources.load_sedlst(self.sedlst)

        # create a pool
        pool=Pool(self.simulate,ncpu=self.ncpu,desc="Simulating FLTs")
        
        # run the pool
        fltnames=pool(grisms.values(),sources,beam)

        #fltnames=[self.simulate(grism,sources,beam) for grism in grisms]

        return fltnames
    
