import numpy as np
from astropy.io import fits
from astropy.table import Table
import fitsimage

import copy
import tqdm

from .source import Source
from .compositesource import CompositeSource
from .directimages import DirectImages
from ..utilities import indices

class SourceCollection(dict):
    PREFIX='{:6d}'
    def __init__(self,segfile,obscat,detindex=0,cubeid=0,maglim=26):
        print('[info]Loading source catalog')
        
        # load the observation catalog
        self.obscat=DirectImages(obscat,detindex=detindex)
        
        # save the segfile
        self.segfile=segfile

        # record the magnitude limit for this collection
        self.maglim = maglim
        
        # get the magnitude limit
        print('[debug]implement source filtering')

        # record something for flux cubes
        self.cubeid=cubeid

        
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


                
        # now remove sources outside the valid magnitude limit
        if self.maglim is not None:
            to_delete = [segid for segid in self.keys()
                         if self[segid].mag>self.maglim]
            for segid in to_delete:
                del self[segid]

            
            #segids=self.keys()
            #for segid in segids:
            #    print(self[segid].mag)
            #if self[segid].mag > self.maglim:
            #         print('[warn]Removing {}, below magnitude limit'.format(self.maglim))
            #          del self[segid]

                    

                
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


        print('[info]Loaded {} sources'.format(len(self)))       


    
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
        del revind[0]    # remove the sky from the segmentation map
        #if revind[0][0]==0:
        #    del revind[0]    # remove the sky from the segmentation map


        # build a progress bar
        pb=tqdm.tqdm(total=len(revind),dynamic_ncols=True,desc='Classic segmap')

        # get the zeropoint
        zeropoint=self.obscat.detzero
        
        # process each index
        #for segid,ri in revind:
        for segid,ri in revind.items():
            pb.desc=self.PREFIX.format(segid)
          
            # get the (x,y) pairs
            x,y=indices.one2two(ri,np.flip(seg.shape))


            # get bounding box
            bbox=(np.amin(x),np.amax(x),np.amin(y),np.amax(y)) 
            
            # call something like hextract
            subseg=seg.extract(*bbox)
            subimg=img.extract(*bbox)

            
            # check for a cube ID
            if segid==self.cubeid:
                print('[debug]This is hardcoded for a single-pixel region')

                self.composite=CompositeSource(segid,subseg)


                
                #y,x=np.mgrid[0:ny,0:nx]
                # y//=dy
                # x//=dx
                # xx,yy are pairs for new seg regions
                
                print('[info]Preparing cube-extraction for: {}'.format(segid))

                for xx,yy,ss in zip(x,y,ri):

                    bbox=(xx,xx,yy,yy)
                    
                    # call something like hextract
                    subseg=seg.extract(*bbox)
                    subimg=img.extract(*bbox)
                    subid=-ss
                    
                    # put the segID in the header for safe keeping
                    subseg.image.fill(subid)
                    subseg['SEGID']=(subid,'Segmentation ID from pylinear')
                          
                    # create the source
                    src=Source(subimg,subseg,zeropoint,minpix=1)
                    if src.valid:
                        self[subid]=src
                        self.composite[subid]=bbox   # record the bounding box
                        
                # reset the segid to create a unique entry
                #segid=-indices.two2one(x,y,dim)
            else:

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

        if hasattr(self,'composite'):
            if self.composite.lamb0 is None:
                self.composite.lamb0=lamb0
            if self.composite.lamb1 is None:
                self.composite.lamb1=lamb1
            if self.composite.dlamb is None:
                self.composite.dlamb=dlamb

                
    def load_sedlst(self,sedlst,seddir='simulated_SEDs',saveseds=True):
        # get the photflam
        bandpass=self.obscat.detband

        # read the SEDLST
        names=('segid','sedfile')
        table=Table.read(sedlst,names=names,format='ascii.no_header')

        # process each segid
        for segid,sedfile in table.iterrows():
            if segid in self:
                self[segid].load_SED(sedfile,bandpass)
            
                if saveseds:
                    self[segid].write_sed(seddir=seddir)
