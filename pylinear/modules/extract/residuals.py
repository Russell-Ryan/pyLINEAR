import numpy as np
from astropy.io import fits
from ...config import Config
from .. import header_utils
from ...utilities import gzip


class ResidualFile(object):
    def __init__(self,flt):
        # save the filename
        self.dataset=flt.dataset
        self.fltfile=flt.filename
        
        # save the methods to load images
        self.loaders={}

        
        # record the nubmer of devices
        #self.ndevice=len(flt)
        #self.unc_images={}
        


        # make a 0th extension
        phdr=fits.Header()

        # put in the config
        Config().update_header(phdr)

        # put in the comments
        header_utils.add_disclaimer(phdr)


        # make an HDUList to put the new extensions into
        hdul=fits.HDUList()
        hdul.append(fits.PrimaryHDU(header=phdr))

        
        # process each device in the FLT
        for i,device in enumerate(flt):
            # define an extver (not sure, but let's avoid extver=0)
            extver=i+1

            # record the loading methids
            self.loaders[device.name]={'uncertainty':device.load_uncertainty,
                                       'dataquality':device.load_dataquality}
                                       
            # read some images to start things
            sci,scihdr=device.load_science()
            dqa,dqaunc=device.load_dataquality()
            
            # make the science (by just copying over the data)
            scihdr['EXTVER']=extver
            hdul.append(fits.ImageHDU(sci,header=scihdr))
            dtype=np.dtype(sci.dtype.name)

            # make the model
            mod=np.zeros_like(sci)
            modhdr=scihdr
            modhdr['EXTNAME']='MODEL'
            modhdr['EXTVER']=extver
            hdul.append(fits.ImageHDU(mod,header=modhdr))


            # make the residual (but at this point the model is just zero,
            # so we will just put the sci image here as:
            # Residual = SCI - MODEL
            res=sci.copy()
            msk=np.bitwise_and(dqa,device.bitmask)!=0
            res[msk]=np.nan
            reshdr=scihdr
            reshdr['EXTNAME']='RESID'
            reshdr['EXTVER']=extver
            hdul.append(fits.ImageHDU(res,header=reshdr))

        # write the file to disk
        hdul.writeto(self.filename,overwrite=True)


    def apply_uncertainty(self):
        with fits.open(self.filename,mode='update') as hdul:
            for i,(devname,loaders) in enumerate(self.loaders.items()):
                #modext=3*i+2                    
                #resext=3*i+3
                extver=i+1
                modext=('MODEL',extver)
                resext=('RESID',extver)
                #modext='MODEL'
                #resext='RESID'
                
                unc,unchdr=loaders['uncertainty']()

                
                hdul[modext].data*=unc
                hdul[resext].data-=hdul[modext].data
            hdul.writeto(self.filename,overwrite=True)
            hdul.flush()
        
    def __str__(self):
        return "residual file for: {}".format(self.dataset)

    def __len__(self):
        return 3*len(self.unc_images)   # 3 here is for the (SCI, MOD, RES)

    #def __del__(self):
    #    self.apply_uncertainty()

    @property
    def filename(self):
        return '{}_res.fits'.format(self.dataset)
    
    def update_model(self,model):
        with fits.open(self.filename,mode='update') as hdul:
            for i,(devname,loaders) in enumerate(self.loaders.items()):
                if devname in model:
                    # get the device data
                    devmod=model[devname]
                    
                    # compute the extensions
                    #sciext=3*i+1    # not really used
                    modext=3*i+2
                    modext=('MODEL',i+1)
                    #resext=3*i+3

                    # update the model (but recall!!! This is needs to be
                    # scaled up by the uncertainty image.  This will be
                    # done in a separate method to avoid reading an
                    # uncertainty image at each iteration.
                    hdul[modext].data[devmod['y'],devmod['x']]+=devmod['v']

            hdul.writeto(self.filename,overwrite=True)

            
class Residuals(object):
    def __init__(self,grisms):
        self.residuals={grism.dataset: ResidualFile(grism) for grism in grisms}

    def __iter__(self):
        yield from self.residuals.values()

        
    def update_model(self,matrix,x):
        
        model=matrix.compute_model(x)
        for dataset,residual in self.residuals.items():
            if dataset in model:
                residual.update_model(model[dataset])
       
    def __iter__(self):
        yield from self.residuals.values()


    def apply_uncertainty(self):
        #for residual in self.residuals.values():
        #    residual.apply_uncertainty()
        #map(lambda resid: resid.apply_uncertainty(),self.residuals.values())
        _=[resid.apply_uncertainty() for resid in self.residuals.values()]

    def gzip_files(self):
        for res in self:
            gzip.gzip(res.filename)

        
if __name__=='__main__':
    x=ResidualFile('test')

    
