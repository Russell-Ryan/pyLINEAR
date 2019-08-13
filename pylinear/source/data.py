import os
import numpy as np
from astropy.io import fits
from collections import OrderedDict
import copy

from .source import Source
from .obslst import ObsLST
from pylinear.astro import fitsimage
from pylinear.utilities import indices


class Data(object):
    SEGTYPE=np.uint32           # force SEGIDs to have this type
    
    def __init__(self,conf):
        print('[info]Loading OBSLST')
        
        # load the obs data
        self.obsdata=ObsLST(conf)

        # save the segmap
        self.segmap=conf['segmap']
        
        # load the segmentation map
        self.sources=OrderedDict()
        
        # read the segmentation map
        with fits.open(self.segmap) as hdus:

            # read the detection image
            with fits.open(self.obsdata.detImage) as hdui:

                # require that the detection & segmentation images are
                # compatable
                assert (len(hdus) == len(hdui)),'Invalid image dimensions'

                # load according to how many extensions
                if len(hdus)==1:
                    self.fromClassic(conf,hdus,hdui)
                else:
                    self.fromMEF(conf,hdus,hdui)


        # rmeove sources below the magnitude limit
        try:
            self.maglimit=conf['maglim']
        except:
            self.maglimit=None
        self.applyMagLimit(self.maglimit)
        

        # set the default spectra as photometry
        self.loadPhotometry()


        # verify some things
        if not self.sources:
            raise RuntimeError("No sources are valid.")
        
    def __contains__(self,key):
        return key in self.sources 
    
    def __len__(self):
        return len(self.sources)

    def __str__(self):
        t='{} sources: \n'.format(str(len(self.sources)))
        t=t+str(list(self.sources.keys()))
        return t

    def __iter__(self):
        yield from self.sources.items()


    def __getitem__(self,segid):
        return self.sources[segid]
    def __setitem__(self,segid,src):
        if isinstance(src,Source):
            if segid in self.sources:
                print("[alarm]Duplicate SEGIDs are ignored: {}".format(segid))
            else:
                if src.valid:
                    self.sources[self.SEGTYPE(segid)]=src
            
    def keys(self):
        return self.sources.keys()

    def values(self):
        return list(self.sources.values())

    def select(self,segids):
        new=copy.deepcopy(self)
        new.sources={segid: self.sources[segid] for segid in segids}
        return new

    

    def loadPhotometry(self):
        ''' load photometry for each source as a crude SED '''
        print('[info]Loading broadband phototmetry')


        fluxunit=1.    # the old way... will deprecate in time.
        
        lamb,flam=[],[]

        for name,filt,zero in self.obsdata:
            lamb.append(filt.photplam)
            img=fitsimage.FitsImage(name)
            f=[]
            for segid,src in self.sources.items():
                tot=src.instrumentalFlux(img)
                f.append(tot*(filt.photflam/fluxunit))
            flam.append(f)

        lamb=np.array(lamb)
        flam=list(zip(*flam))

        for (segid,src),f in zip(self.sources.items(),flam):
            src.sed.lamb=lamb
            src.sed.flam=np.array(f)
            

    def applyMagLimit(self,maglimit):
        ''' apply a magnitude limit cut '''
            
        if maglimit is not None:
            print('[info]Apply magnitude limit: {}'.format(maglimit))
            sources=OrderedDict()
            for segid,src in self.sources.items():
                if src.mag < maglimit:
                    sources[segid]=src
            n=len(sources)
            if n==0:
                raise RuntimeError("All sources too faint.")

            print('[info]Magnitude limit: {} -> {}'.format(len(self),n))
            self.sources=sources

            

    def fromClassic(self,conf,seglist,imglist):
        ''' load sources via a classic segmentation map '''
        print('[info]Loading sources from CLASSIC segmentation map')

        # load the images
        seg=fitsimage.FitsImage()
        seg.loadHDU(seglist[0])

        img=fitsimage.FitsImage()
        img.loadHDU(imglist[0])


        # get the reverse indices (is potentially slow)
        revind=indices.reverse(seg.data.astype(self.SEGTYPE))
        if revind[0][0]==0:
            del revind[0]     # remove the sky index from the segmentation


        # get the detection filter
        detzpt=self.obsdata.detZeropoint
            
        # process each index
        for segid,ri in revind:
            # compute (x,y) pairs
            x,y=indices.one2two(ri,seg.naxis)

            # get bounding box
            x0,x1=np.amin(x),np.amax(x)
            y0,y1=np.amin(y),np.amax(y)
            
            # call something like hextract
            subseg=seg.extract(x0,x1,y0,y1)
            subimg=img.extract(x0,x1,y0,y1)
            
            # put the segID in the header
            subseg['SEGID']=segid

            # create the source
            self[segid]=Source(subimg,subseg,detzpt,segid=segid,\
                               maglim=conf['maglim'],minpix=conf['minpix'])

        
        


    def fromMEF(self,conf,seglist,imglist):
        ''' load sources via a multi-extension fits file '''

        print('[info]Loading sources from MEF segmentation map')
        

        keyword=lambda key,hdu:hdu.header[key] if key in hdu.header else None

        
        detzpt=self.obsdata.detZeropoint
        for seghdu,imghdu in zip(seglist,imglist):
            src=Source(imghdu,seghdu,detzpt,
                       lamb0=keyword('LAMB0',seghdu),\
                       lamb1=keyword('LAMB1',seghdu),\
                       dlamb=keyword('DLAMB',seghdu),\
                       maglim=conf['maglim'],minpix=conf['minpix'])
            self[src.segid]=src
                
                

    
