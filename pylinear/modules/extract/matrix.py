
import numpy as np
import tqdm
import h5py
import os
import scipy.sparse.linalg as ssl
from scipy.sparse import coo_matrix


from .. import header_utils
from ...utilities import indices
from ... import h5table
from ...constants import COMPARGS
from .lcurve import LCurve
from .result import Result
from .fluxunit import FLUXSCALE

class Matrix(object):
    INT=np.uint64
    FLOAT=np.float64
    MINUNC=1e-10

    #grisms,sources,extbeams,usehdf5=False,hdf5file='matrix.h5'
    def __init__(self,*args,group=0,inverter='lsqr',mskbeams=None,
                 path='tables'):

        # parse the inputs
        n=len(args)
        if n==3:
            grisms,sources,extbeams=args
        else:
            return
        
        
        # set some defaults        
        self.group=group
        self.path=os.path.join(path)
        self.target=None
       
        # get some dimensions
        self.nimg=len(grisms)
        self.nsrc=len(sources)

        # size of a grism image
        self.imgdim=None   # (nx,ny)

        # set the inversion scheme
        self.inverter=inverter

        
        # compute the number of wavelengths to extract
        nwav=[src.nwavelength() for src in sources]
        cwav=np.cumsum(nwav)     # get the cumulative indices

        # number of parameters
        self.npar=cwav[-1]       # max number of wavelengths to determine
        self.cwav=np.insert(cwav,0,0)
        
        # index for the image in question
        self.images=[]    #self.images.append((grism.dataset,device.name))
        
        # load the matrix data
        #if usehdf5:
        #    i,j,aij,self.bi=self.load_from_hdf5(grisms,sources,extbeams,
        #                                        mskbeams,hdf5file)
        #else:
        #    i,j,aij,self.bi=self.load_from_images(grisms,sources,extbeams,
        #                                          mskbeams,hdf5file)
        i,j,aij,self.bi=self.load_from_images(grisms,sources,extbeams,mskbeams)
                                              

        # just do a quick check
        if len(i)==0:
            print('[alarm]Matrix has no elements.')
            return

       
        # everthing is loaded, so let's juggle the indices
        print('[info]Compressing the indices')
        self.icomp,self.iuniq=indices.compress(i)
        self.jcomp,self.juniq=indices.compress(j)
        
        #original lines
        #ic,iu=indices.compress(i)
        #jc,ju=indices.compress(j)

        # get some dimensionalities
        ni=len(self.iuniq)
        nj=len(self.juniq)
        dim=np.array([ni,nj],dtype=self.INT)

        # do a quick check
        if np.amax(self.icomp)!=len(self.bi)-1:
            print('[warn]Invalid dimensionality in matrix')

        
        # the datatype of the j (used a lot)
        jtype=self.juniq.dtype

        # total number of wavelenghts *actually present* in the matrix
        self.npix=dim[0]
        self.npar=dim[1]
        
        if self.npar>=self.npix:            
            print('')
            print('[alarm]Underdetermined matrix!!!')
            print('[alarm]There are {} measurments and {} unknowns.'.format(*dim))
            print('[alarm]pyLINEAR can invert, but results will be suspect.')
            print('')
            
        
        # compute some things for the ragged arrays
        if self.nsrc==1:
            srcind=np.zeros(self.npar,dtype=jtype)
        else:
            srcind=np.digitize(self.juniq,self.cwav)-1

        # get the wavelength indices for each of the sources
        try:
            self.lam=self.juniq-self.cwav[srcind]
        except:
            print(ni,nj,self.nsrc)
            print('[debug]Something is fishy in matrix.py')
            import pdb
            pdb.set_trace()

        # get the reverse indices
        self.segids = list(sources.keys())
        self.ri=indices.reverse(np.array(self.segids,dtype=int)[srcind])
        self.hsrc = np.bincount(srcind.astype(np.int)).astype(self.INT)

        # compute the frobenius norm (used when calling LSQR)
        # this could be avoided if we collect sum(aij^2) along the way
        self.frob=np.sqrt(sum(a*a for a in aij))


        
        # ok... finally... Package up the matrix as a coo_matrix
        self.A=ssl.aslinearoperator(coo_matrix((aij,(self.icomp,self.jcomp)),
                                               shape=dim))




        #g=np.where(self.A.A.col == 0)[0]
        
        
        #ii=self.A.A.row[g]
        #jj=self.A.A.col[g]
        #aij=self.A.A.data[g]
        #tot=np.sum(aij*aij)
        #u=1./np.sqrt(tot)
        #print(ii,jj,u)
        #print(unc)
        #import pdb
        #pdb.set_trace()

        #iic,iiu=indices.compress(ii)
        #jjc,jju=indices.compress(jj)
        
        #dim=np.array([max(iic),max(jjc)])+1
        
        # compute the density of this matrix
        self.density=float(self.A.A.nnz)/(float(dim[0])*float(dim[1]))

        # now we want to create an Lcurve for this matrix
        self.lcurve=LCurve(norm=self.frob)


    def __len__(self):
        if hasattr(self,'A'):
            return self.A.A.nnz
        else:
            return 0
        
    #def load_from_hdf5(self,grisms,sources,extbeams,mskbeams,hdf5file):
    #    msg='[info]Loading the matrix from {}'
    #    #print(msg.format(hdf5file))
    #    
    #    print('[debug]Check if the inputs match')
    #    
    #    pb=tqdm.tqdm(total=self.nimg,desc='Loading matrix',dynamic_ncols=True)
    #    
    #    i,j,aij,bi=[],[],[],[]
    #    
    #    with h5py.File(hdf5file,'r') as h5:
    #        hg=h5['grisms']
    #        for grism in grisms:
    #            pb.update()
    #
    #            hd=hg[grism.dataset]
    #            if 'aij' in hd and 'bi' in hd:
    #
    #                mat=hd['aij'][:]
    #                i.extend(list(mat['i']))
    #                j.extend(list(mat['j']))
    #                aij.extend(list(mat['aij']))
    #                vec=hd['bi'][:]
    #                bi.extend(list(vec))
    #
    #    # retype things
    #    i=np.array(i,dtype=self.INT)
    #    j=np.array(j,dtype=self.INT)
    #    aij=np.array(aij,dtype=self.FLOAT)
    #    bi=np.array(bi,dtype=self.FLOAT)
    #                
    #    return i,j,aij,bi
    
    def load_from_images(self,grisms,sources,extbeams,mskbeams):
        msg='[info]Building the matrix: {} images, {} sources.'
        print(msg.format(self.nimg,self.nsrc))

        
        # make a progress bar
        pb=tqdm.tqdm(total=self.nimg,desc='Loading ODTs',dynamic_ncols=True)

        # open a file to write to
        # data to save as the matrix content
        i,j,aij,bi=[],[],[],[]

        # process each grism image        
        for grism in grisms:
            pb.update()     # update the progess bar
            
            # load the data from a single grism image
            data=self.load_grism(grism,sources,extbeams,mskbeams)
                        
            # collect the matrix values
            if len(data[0]) > 0:
                i.extend(data[0])
                j.extend(data[1])
                aij.extend(data[2])
                bi.extend(data[3])

        # retype things
        i=np.array(i,dtype=self.INT)
        j=np.array(j,dtype=self.INT)
        aij=np.array(aij,dtype=self.FLOAT)
        bi=np.array(bi,dtype=self.FLOAT)

        return i,j,aij,bi


        
    def make_beam_mask(self,h5tab,sources,device,mskbeams,min_rate=1e-2):
        ''' compute a mask to exclude pixels associated with other beams '''
                
        # get the photflam
        photflam=sources.obscat.detband.photflam
        
        # make output beam amsk
        beam_mask=np.zeros([device.naxis2,device.naxis1],dtype=bool)

        # load the config
        configs=[device.load_beam(beam) for beam in mskbeams]

        # process each source
        for source in sources:
            # the notional flux of a source
            flam=source.total*photflam

            # process each beam
            for config in configs:

                # open the OMT
                h5tab.open_table(device.name,config.beam,'omt')
                
                # a notional peak count rate in a grism image
                count_rate=flam*config.sensitivity.smax

                # only mask the pixels if the source is bright enough
                if count_rate > min_rate:

                    # read the OMT
                    #omt=h5tab.load_from_file(source.name,'omt',config.beam)
                    omt=h5tab.load_from_file(source,config.beam,'omt')
                    
                    # put values in beam_mask
                    beam_mask[omt.y.to_numpy(),omt.x.to_numpy()]=True

        return beam_mask
        
        
    def load_grism(self,grism,sources,extbeams,mskbeams):

        # stuff to output
        i,j,aij,bi=[],[],[],[]
        
        # open the ODT file
        dataset=grism.dataset
        with h5table.H5Table(dataset,path=self.path,mode='r') as h5tab:
            for device in grism:
                # read the images
                sci,hsci=device.load_science()
                unc,hunc=device.load_uncertainty()
                dqa,hdqa=device.load_dataquality()

                # make a mask  (these are good pixels)
                msk=np.bitwise_and(dqa,device.bitmask)==0


                
                # update the mask with the beams
                #if mskbeams is not None and mskbeams:
                if mskbeams:
                    msk |= self.make_beam_mask(h5tab,sources,device,mskbeams)

                # total number of pixels in the image
                npix=self.INT(device.naxis1)*self.INT(device.naxis2)


                # set the image dimensions, and make sure it's fixed
                imgdim=(device.naxis1,device.naxis2)
                if self.imgdim is None:
                    self.imgdim=imgdim
                elif self.imgdim!=imgdim:
                    raise RuntimeError("Detector size must not change.")
                    
                # load the right device
                #h5tab.open_device(device.name)  
                
                # load beam configurations and flat fields
                config={}
                for beam in extbeams:
                    beamconf=device.load_beam(beam)
                    flatfield=beamconf.load_flatfield()
                    config[beam]=(beamconf,flatfield)


                # container for the xy pairs
                xygp=[]


                
                # process each source
                for kk,source in enumerate(sources):
                    
                    # this takes ODTs, decimates, scales by detector
                    # effects, and joins them over beams
                    ddt=self.load_ddts(source,unc,device,h5tab,config)
                    
                    # apply the DQA+beam mask
                    ddt.apply_mask(msk)

                    
                    # now will need to decimate the DDTs
                    # this is a null operation for detectors where the
                    # multiple beam orders do not overlap, but when they
                    # do, this is important (ie. UVIS, NIRISS/SOSS)
                    if len(ddt)>0:
                        # dump the table just for easier work
                        x=ddt.x.astype(self.INT)
                        y=ddt.y.astype(self.INT)
                        
                        # get the wavelength ranges
                        limits=source.limits()
                        
                        # compute the indices for the wavelength bins
                        lamind=np.digitize(ddt.wav,limits)-1
                        lamind=lamind.astype(self.INT)

                        # 1d pixel coordinate in grism frame
                        xyg=x+device.naxis1*y
                        
                        # compute 2d matrix coordinates
                        imgindex=self.INT(len(self.images))
                        ii=xyg+npix*imgindex
                        jj=lamind+self.cwav[kk]
                        
                        # compute 1d matrix coordinate
                        ij=jj+self.npar*ii  # this inverted w.r.t. my talks

                        #decimate over repeated indices
                        aiju,iju=indices.decimate(ij,ddt.val.astype(self.FLOAT))

                        # compute the 2d matrix coordinates from the
                        # unique 'u' 1d coordinates (iju)
                        iu,ju=np.divmod(iju,self.npar)
                        
                        # compute the 1d pixel positions
                        imgu,xygu = np.divmod(iu,npix)

                        # remove duplicates (but preserve order)
                        xygu=indices.unique(xygu)

                        '''
                        # convert from 1d coords to 2d image coords
                        xg,yg=indices.one2two(xygu,device.shape)

                        # retype things because I've seen funkiness before
                        xg=xg.astype(self.INT)
                        yg=yg.astype(self.INT)

                        # get the vector values
                        biu=sci[yg,xg]/unc[yg,xg]

                        # do some error checking
                        assert not any(np.isinf(biu)),'Infinite S/N found. is UNC image ok?'
                        '''
                        
                        # at this point, the relevant data are:
                        #    (aij,(iu,ju)) for the matrix
                        #     biu for the vector
                        # so let's package them for output
                        i.extend(iu)
                        j.extend(ju)
                        aij.extend(aiju)
                        #bi.extend(biu)
                        xygp.extend(xygu)


                ########################################################

                # make into a numpy array
                xygp=np.array(xygp)
                
                # ok, now get the values for the vector
                # from the unique grism pixel pairs (xygp)
                
                # due to differences in the way np.unique and
                # IDL's uniq work, this line is necessary
                xygp=np.sort(xygp)
                
                # uniqify thse pairs
                xygp=indices.unique(xygp)
                        
                # convert from 1d coords to 2d image coords
                xg,yg=indices.one2two(xygp,device.shape)
                
                # retype things because I've seen funkiness before
                xg=xg.astype(self.INT)
                yg=yg.astype(self.INT)
                
                # update the vector values
                bi.extend(sci[yg,xg]/np.maximum(unc[yg,xg],self.MINUNC))
                ########################################################
                        
                # close the device (could avoid this by restructuring h5table)
                #h5tab.close_device()
                
                # update the images list
                self.images.append((dataset,device.name))


        # return the matrix data
        return i,j,aij,bi

                    

    def load_ddts(self,source,unc,device,h5tab,config,threshold=None):
        ''' make DDTs for detector effects '''
        
        # this is the thing that is the output
        source_ddt=h5table.DDT(source.segid)

        
        # this is to join the DDTs for all the beams
        for beam,(beamconf,flatfield) in config.items():
            h5tab.open_table(device.name,beam,'pdt')

            # read the table
            #odt=h5tab.load_from_file(source.name,'odt',beam)
            odt=h5tab.load_from_file(source,beam,'odt')

            # decimate 
            ddt=odt.decimate(device.naxis1,device.naxis2)
            
            # bin the DDT by output wavelength bin
            if len(ddt) != 0:
                
                # compute the wavelength bins for the source
                limits=source.limits()
                wav0=np.amin(limits)
                wav1=np.amax(limits)                       
               
                # remove the pixels beyond the range
                g=np.where((ddt.wav >= wav0) & (ddt.wav <= wav1))[0]
                ddt.select(g)
                        
                # just for streamlined access
                x=ddt.x.to_numpy()
                y=ddt.y.to_numpy()
                wav=ddt.wav.to_numpy()
                            
                # compute a few things to scale the tables
                # 1. sensitivity curve
                # 2. flat field
                # 3. PAM.  (will do later, since that's not
                #           given as a wave-depend. thing)
                s=beamconf.sensitivity(wav)*FLUXSCALE
                f=flatfield(x,y,wav)
                p=device.pixel_area_map(x,y)
                                
                # scale the DDT
                ddt*=(s*f*p)

                # apply a threshold
                if threshold is not None:
                    ddt.threshold(threshold)
                        
                # compute the wavlength indices
                #lamind=np.digitize(ddt.wav,limits)-1
                
                           
                # scale the matrix elements by the uncertainties
                ddt/=np.maximum(unc[y,x],self.MINUNC)
                                                    
                # join the DDT
                source_ddt.extend_with_ddt(ddt)
                            

                

                '''
                # compute the 2d matrix coordinates
                xy=x.astype(self.INT)+device.naxis1*y.astype(self.INT)
                ii=xy+npix*imgindex      # imgindex is l
                jj=lamind+self.cwav[kk]  
                
                # compute 1d matrix coordinate
                ij=jj+self.npar*ii     # inverted w.r.t. talks
                
                
                # decimate over repeated indices
                aiju,iju=indices.decimate(ij,ddt.val.to_numpy())
                
                # compute the 2d matrix coordinates
                iu,ju=np.divmod(iju,self.npar)
                
                # compute the pixel positions
                imgind,xygind=np.divmod(iu,npix)
                
                # remove duplicates from the 1d pixel positions
                xyu=indices.unique(xygind)
                
                # retype things to avoid overflow errors
                iu=iu.astype(self.INT)
                ju=ju.astype(self.INT)
                aiju=aiju.astype(self.FLOAT)
                xyu=xyu.astype(self.INT)
                '''
                            
        return source_ddt

    def set_damping_target(self,target):
        self.target=target
        self.bi-=self.A.matvec(self.target)


    def invert(self,logdamp,scale=True,**kwargs):
        if self.inverter=='lsqr':
            return self.run_lsqr(logdamp,scale=scale,**kwargs)
        elif self.inverter=='lsmr':
            return self.run_lsmr(logdamp,scale=scale,**kwargs)
        else:
            raise NotImplementedError("Inverter not found.")
    
        
    
    def run_lsmr(self,logdamp,scale=True,**kwargs):
        # scale the log(damp) into a damping
        if logdamp is None:
            damp=0.
        else:
            damp=10.**logdamp
            if scale:
                damp*=self.frob   # scale the damping by frobenius
        print('[info]Running LSMR with l={}'.format(damp))
        
        #t1=default_timer()
        r=ssl.lsmr(self.A,self.bi,damp=damp,**kwargs)
        (x,istop,itn,normr,normar,norma,conda,normx)=r
        
        r1norm=normr
        r2norm=np.sqrt(normr**2+(damp*normx)**2)
        lo=np.zeros_like(x)
        hi=np.zeros_like(x)
        r=Result('lsmr',x,istop,itn,r1norm,r2norm,norma,conda,normar,normx,
                 lo,hi,damp/self.frob)
        #t2=default_timer()
        #dt=(t2-t1)/60.    # in minutes
        
        self.lcurve.append(r.r1norm,r.xnorm,r.logdamp)

        return r


        
        
    def run_lsqr(self,logdamp,scale=True,**kwargs):

        # scale the log(damp) into a damping
        if logdamp is None:
            damp=0.
        else:
            damp=10.**logdamp
            if scale:
                damp*=self.frob   # scale the damping by frobenius

        print('[info]Running LSQR with l={}'.format(damp))
        
        #t1=default_timer()
        r=ssl.lsqr(self.A,self.bi,damp=damp,calc_var=True,**kwargs)

                
        #atol=atol,btol=btol,conlim=conlim,iter_lim=maxiter)#
        
                   #,show=show,
        
        #t2=default_timer()
        #dt=(t2-t1)/60.    # in minutes

        # take the target out
        if self.target is not None:
            r=(r[0]+self.target,*r[1:])
            
        # package the outputs
        r=Result('lsqr',*r,r[-1].copy(),damp/self.frob)
        
        
        # update the Lcurve
        self.lcurve.append(r.r1norm,r.xnorm,r.logdamp)
        

        return r


    def estimate_uncertainty(self):

        ai2,j2=indices.decimate(self.juniq[self.jcomp],
                                self.A.A.data*self.A.A.data)

        # these two lines to avoid divide-by-zero errors
        unc=np.full_like(ai2,np.inf)
        np.divide(1.,np.sqrt(ai2),out=unc,where=(ai2!=0))

        # original line
        #unc=1./np.sqrt(ai2)

        return unc
    

    def sub_matrix(self,j,resid):
      
        g=np.where(self.A.A.col == j)[0]
        
        if len(g)==0:
            print('[warn]No valid matrix elements for column={}'.format(j))
            return None,None
        
        ii=self.A.A.row[g]
        jj=self.A.A.col[g]
        aij=self.A.A.data[g]
        iic,iiu=indices.compress(ii)
        jjc,jju=indices.compress(jj)
 
        dim=np.array([max(iic),max(jjc)])+1



        #tot=np.sum(aij*aij)
        #unc=1/np.sqrt(tot)

        A=ssl.aslinearoperator(coo_matrix((aij,(iic,jjc)),shape=dim))
        try:
            bi=resid[iic]
        except:
            print(len(resid))
            print(iic)
            print(j)
            print(len(iic),len(iiu))
            import pdb
            pdb.set_trace()

            
        return A,bi



    def compute_model(self,xj):
        bi=self.A.matvec(xj)

        npix=self.imgdim[0]*self.imgdim[1]
        imgindices,pixindices=np.divmod(self.iuniq,npix)


        dtype=[('x',np.uint16),('y',np.uint16),('v',np.float64)]

        out={image:{} for (image,detname) in self.images}
        for imgindex,(image,detname) in enumerate(self.images):
            g=np.where(imgindices == imgindex)
            
            y,x=np.divmod(pixindices[g],self.imgdim[0])
            data=np.array(list(zip(x,y,bi[g])),dtype=dtype)
            out[image][detname]=data

        return out

    
    def update_header(self,hdr):
        getint = lambda k: int(getattr(self,k)) if hasattr(self,k) else int(0)
        getflt = lambda k: float(getattr(self,k)) if hasattr(self,k) else 0.0
        getnan = lambda k: getattr(self,k) if hasattr(self,k) else 'NaN'
        
        after=header_utils.get_last_keyword(hdr)
                
        hdr.set('NNZ',value=len(self),after=after,#self.A.A.nnz,after=after,
                comment='total number of non-zero matrix elements')
        hdr.set('NPIXEL',value=getint('npix'),after='NNZ',
                comment='total number of pixels analyzed')
        hdr.set('NSOURCE',value=getint('nsrc'),after='NPIXEL',
                comment='total number of sources analyzed')
        hdr.set('NWAVE',value=getint('npar'),after='NSOURCE',
                comment='total number of wavelengths extracted')
        hdr.set('DENSITY',value=getnan('density'),after='NWAVE',
                comment='fraction of non-zero elements')
        hdr.set('FROBNORM',value=getflt('frob'),after='DENSITY',
                comment='Frobenius norm')
        hdr.set('NDOF',getint('npix')-getint('npar'),after='FROBNORM',
                comment='number of degrees of freedom (=NPIXEL-NWAVE)')
        header_utils.add_stanza(hdr,'Matrix Properties',before='NNZ')


    def to_hdf5(self,h5):
        name=str(self.group)
        hf=h5.require_group(str(self.group))

        hf.attrs['frob']=self.frob
        hf.attrs['path']=self.path
        hf.attrs['nimg']=self.nimg
        hf.attrs['nsrc']=self.nsrc
        hf.attrs['imgdim']=self.imgdim
        hf.attrs['inverter']=self.inverter
        hf.attrs['npix']=self.npix
        hf.attrs['npar']=self.npar
        hf.attrs['density']=self.density


        # flags for writing dataset

        # write all the datasets
        d=hf.create_dataset('icomp',data=self.icomp,**COMPARGS)
        d=hf.create_dataset('iuniq',data=self.iuniq,**COMPARGS)
        d=hf.create_dataset('jcomp',data=self.jcomp,**COMPARGS)
        d=hf.create_dataset('juniq',data=self.juniq,**COMPARGS)
        d=hf.create_dataset('cwav',data=self.cwav,**COMPARGS)
        d=hf.create_dataset('lam',data=self.lam,**COMPARGS)
        d=hf.create_dataset('segids',data=self.segids,**COMPARGS)
        
        
        dtype=[('dataset','S36'),('device','S36')]        
        d=hf.create_dataset('images',data=np.array(self.images,dtype=dtype),
                            **COMPARGS)
        
        # the reverse indices dict is ragged, so will encode the
        # segid in there as the first element of a list
        dtype=h5py.vlen_dtype(np.dtype('uint64'))
        d=hf.create_dataset('ri',(len(self.ri),),dtype=dtype,**COMPARGS)
        for i,segid in enumerate(self.ri.keys()):
            d[i]=self.ri[segid]
            #d[i]=[segid]+ri
        

        
        #d=hf.create_dataset('ri',data=self.ri)
        d=hf.create_dataset('hsrc',data=self.hsrc,**COMPARGS)
        if self.target is not None:
            d=hf.create_dataset('target',data=self.target,**COMPARGS)

        d=hf.create_dataset('bi',data=self.bi,**COMPARGS)
        dtype=[('row',self.INT),('col',self.INT),('data',self.FLOAT)]
        data=np.array(list(zip(self.A.A.row,self.A.A.col,self.A.A.data)),
                      dtype=dtype)

        d=hf.create_dataset('aij',data=data,**COMPARGS)
        d.attrs['shape']=self.A.A.shape


        # write the LCurve results
        self.lcurve.write_hdf5(hf)
        
    @classmethod
    def from_hdf5(cls,h5,group):
        obj=cls()
        obj.group=group
        if str(obj.group) in h5:
            
            hf=h5[str(obj.group)]
            for k,v in hf.attrs.items():
                setattr(obj,k,v)
            obj.imgdim=tuple(obj.imgdim)
            
            obj.icomp=hf['icomp'][:]
            obj.iuniq=hf['iuniq'][:]
            obj.jcomp=hf['jcomp'][:]
            obj.juniq=hf['juniq'][:]
            obj.lam=hf['lam'][:]
            obj.cwav=hf['cwav'][:]
            obj.segids=hf['segids'][:]



            
            decode=lambda x: x.decode('UTF-8')
            images=hf['images'][:]
            obj.images=[(decode(dset),decode(dev)) for dset,dev in images]
            
            
            hd=hf['ri']
            obj.ri={s:hd[i] for i,s in enumerate(obj.segids)}

            obj.hsrc=hf['hsrc'][:]
            if 'target' in hf:
                obj.target=hf['target'][:]
            else:
                obj.target=None

            obj.bi=hf['bi'][:]

            
            shape=hf['aij'].attrs['shape']
            A=hf['aij'][:]
            obj.A=ssl.aslinearoperator(coo_matrix((A['data'],
                                                   (A['row'],A['col'])),
                                                  shape=shape))

            # load the L-curve data and test with the other loaded frob
            obj.lcurve=LCurve.from_hdf5(hf)
            if np.abs(obj.lcurve.norm/obj.frob-1)>1e-4:
                print('[warn]The frobenius norm is corrupted')

            return obj
        else:
            print('[warn]Group missing from matrix.h5')
            

                
    #def write_pickle(self,filename):
    #    print('[info]Pickling the matrix to: {}'.format(filename))
    #    with open(filename,'wb') as fp:
    #        pickle.dump(self,fp)          
    #
    #@classmethod
    #def load_pickle(cls,filename):
    #    print('[info]Unpickling matrix file: {}'.format(filename))
    #    with open(filename,'rb') as fp:
    #        data=pickle.load(fp)
    #    return data

