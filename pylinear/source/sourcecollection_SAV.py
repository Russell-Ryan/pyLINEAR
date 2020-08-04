import numpy as np
from astropy.io import fits
from astropy.table import Table
import fitsimage

import copy
import tqdm

from ..config import Config
from .source import Source
from .directimages import DirectImages
from ..utilities import indices

class SourceCollection(dict):
    PREFIX='{:6d}'
    def __init__(self,segfile,obscat,detindex=0):
        print('[info]Loading source catalog')
        
        # load the observation catalog
        self.obscat=DirectImages(obscat,detindex=detindex)
        
        # save the segfile
        self.segfile=segfile

        # get the magnitude limit
        print('[debug]implement magnitude limit and source filtering')

        
        # figure out which maps:
        detfile=self.obscat.detfile    # just for streamlined access
        with fits.open(self.segfile) as hdus,fits.open(detfile) as hdui:
            nhdus,nhdui=len(hdus),len(hdui)

            
            # require that the detection/segmentation images are compatible
            assert (nhdus==nhdui),'Incompatible segmentation/detection images'

            # load based on the extensions
            mef=nhdus>1
            if mef:
                self.from_mef(hdus,hdui)                
            else:
                self.from_classic(hdus,hdui)

            
        # check for validity
        if len(self)==0:
            msg="There are no valid sources."
            print('[warn]{}'.format(msg))
            raise RuntimeError("{}".format(msg))

        # load the photometry
        # NB: this might seem out of order, and could be put in the
        #     fromClassic and fromMEF modules.  This is technically true,
        #     but would require considerable more file I/O.  
        self.load_photometry(mef)

        print()

    #def ifu_sources(self,ifuid):
    #    if ifuid in self:
    #        source=self.pop(ifuid)
    #
    #    else:
    #        raise RuntimeError("IFU ID is invalid")
    #return pixels

    #@classmethod
    #def sourcelist(cls,sources):
    #    pass

    
    def __iter__(self):
        yield from self.values()

    def write_h5(self,hs):        
        hs.attrs['segfile']=np.string_(self.segfile)
        hs.attrs['imgfile']=np.string_(self.obscat.detfile)
        for source in self:
            source.write_h5(hs)
                  
        
        
    #def select(self,segids):
        #out=copy.deepcopy(self)      # create the output
        #out.clear()                  # flush the current dict contents
        #
        ## loop over the segids to keep
        #for segid in segids:
        #    if segid in self:        # only copy the source if it exists
        #        out[segid]=self[segid] #copy.deepcopy(self[segid])
        #return out
    
            
    def load_photometry(self,mef):
        print('[info]Loading broadband photometry')

        lamb,flam=[],[]
        for filename,bandpass in self.obscat.items():
            lamb.append(bandpass.photplam)    # the filter central wave
            photflam=bandpass.photflam        # just a shorthand
                        
            if mef:
                raise NotImplementedError("MEF loading photometry")

            else:
                img=fitsimage.FITSImage(filename,0)   # read the fits iamge
                pflam=bandpass.photflam     # just get the photflam for access
                flux=[src.instrumental_flux(img)*photflam
                      for segid,src in self.items()]                      
            
                flam.append(flux)

        # repackage the data
        lamb=np.array(lamb)
        flam=list(zip(*flam))

        # now record the data to the sources
        for src,flux in zip(self.values(),flam):
            src.set_SED(lamb,flux)
        
            

    def from_classic(self,hdus,hdui):
        print('[info]Loading sources from CLASSIC segmentation map')

        # load the images
        exten=0
        seg=fitsimage.FITSImage(hdus,exten)
        img=fitsimage.FITSImage(hdui,exten)

        # get the reverse index
        revind=indices.reverse(seg.image.astype(np.uint64))
        if revind[0][0]==0:
            del revind[0]    # remove the sky from the segmentation map


        # build a progress bar
        pb=tqdm.tqdm(total=len(revind),dynamic_ncols=True,desc='Classic segmap')

        # get the zeropoint
        zeropoint=self.obscat.detzero
        
        # process each index
        for segid,ri in revind:
            pb.desc=self.PREFIX.format(segid)

            # get the (x,y) pairs
            x,y=indices.one2two(ri,np.flip(seg.shape))

            # get bounding box
            bbox=(np.amin(x),np.amax(x),np.amin(y),np.amax(y))                
            
            # call something like hextract
            subseg=seg.extract(*bbox)
            subimg=img.extract(*bbox)

            # put the segID in the header for safe keeping
            subseg['SEGID']=(segid,'Segmentation ID from pylinear')
            
            # create the source
            src=Source(subimg,subseg,zeropoint)
            if src.valid:
                self[segid]=src
            
            # update
            pb.update()

    def from_mef(self,hdus,hdui):
        raise NotImplementedError

    
    def update_extraction_parameters(self,lamb0,lamb1,dlamb):
        print('[info]updating extraction parameters.')
        for source in self:
            if source.lamb0 is None:
                source.lamb0=lamb0
            if source.lamb1 is None:
                source.lamb1=lamb1
            if source.dlamb is None:
                source.dlamb=dlamb


    def load_sedlst(self,sedlst):
        # get the photflam
        bandpass=self.obscat.detband

        # read the SEDLST
        names=('segid','sedfile')
        table=Table.read(sedlst,names=names,format='ascii.no_header')

        # process each segid
        for segid,sedfile in table.iterrows():
            if segid in self:
                self[segid].load_SED(sedfile,bandpass)

        
