import os
import numpy as np
import timeit
import scipy.sparse.linalg as ssl
from scipy.sparse import coo_matrix

from . import lcurve,lsqrresult
from pylinear import h5table
from pylinear.utilities import progressbar,indices
from .fluxunit import FLUXSCALE

__RAM__ = False

class Matrix(object):
    TTYPE='DDT'            # Which type of table to use
    def __init__(self,conf,grisms,sources,extconf,mskconf,grismFF):
        
        # dimensionalities
        self.nimg=len(grisms)
        self.nsrc=len(sources)

        # print a message
        msg="[info]Building the matrix: {} images, {} sources"
        print(msg.format(self.nimg,self.nsrc))
        
        # stuff for LSQR
        lsqrconf=conf['lsqr']
        self.atol=float(lsqrconf['atol'])
        self.btol=float(lsqrconf['btol'])
        self.conlim=float(lsqrconf['conlim'])
        self.maxiter=lsqrconf['maxiter']
        self.show=lsqrconf['show']
        
        # double check the type of maxiter
        if self.maxiter is not None:
            self.maxiter=int(self.maxiter)
            
        ## get extraction properties for the sources
        #nwav=[]
        #for segid,src in sources:
        #    for key in ['lamb0','lamb1','dlamb']:
        #        self.epar2(src,conf,extconf,key)
        #    #if src.lamb0 is None: src.lamb0=self.epar(conf,extconf,'lamb0')
        #    #if src.lamb1 is None: src.lamb1=self.epar(conf,extconf,'lamb1')
        #    #if src.dlamb is None: src.dlamb=self.epar(conf,extconf,'dlamb')
        #    nwav.append(src.nwav)


        # get number of wavelengths to use
        nwav=[src.nwav for segid,src in sources]
        cwav=np.cumsum(nwav)    # get cumulative indices
        self.npar=cwav[-1]
        self.cwav=np.array([0,*cwav],dtype=cwav.dtype)
        
        # data to hold matrix/vector stuff
        i,j,aij=[],[],[]

        self.bi=np.array([],float)
        self.downtype=False    # attempt to save space

        # this was like 'i' before.  but now we need to increment for
        # each FLT and detector
        self.imgindex=0

        # just a short hand
        path=conf['tables']['path']
        
        # loop over images
        pb=progressbar.ProgressBar(self.nimg,prefix='Loading ODTs')

        # output values
        if __RAM__:
            import os,psutil      
            pid = os.getpid()
            py = psutil.Process(pid)

        for fltindex,(fltfile,flt) in enumerate(grisms):
            # update the progressbar
            if __RAM__:
                print("top:",py.memory_info()[0]/1024/1024/1024)

            pb.increment()
            
            data=self.loadFLT(flt,sources,extconf,mskconf,grismFF,pb,path)
            
            if __RAM__:
                print("read loadFLT:",py.memory_info()[0]/1024/1024/1024)

            i.append(data[0])
            j.append(data[1])
            aij.append(data[2])
            if __RAM__:
                print("stacked:",py.memory_info()[0]/1024/1024/1024)

        # stacking all the data into a 1D numpy array
        i = np.hstack(i)
        j = np.hstack(j)
        aij = np.hstack(aij)
        if __RAM__:
            print("finished:",py.memory_info()[0]/1024/1024/1024)

        if len(i)==0:
            print('[alarm]Matrix has no elements.')
            #raise RuntimeError("matrix had no elements")
            return
        
        # loaded everything
        print("[info]Compressing the indices")
        ic,iu=indices.compress(i)
        jc,ju=indices.compress(j)
        dim=np.array([len(iu),len(ju)])
        self.npar=dim[1]
        #self.npar=np.amax(ju)+1     # IDL has +1 here (this was an error?)
        self.npar=self.npar.astype(ju.dtype)
        del i,j
        
        
        # compute some things for ragged arrays
        if len(sources)==1:
            #srcind=np.zeros(self.npar+1,dtype=int)
            srcind=np.zeros(self.npar,dtype=ju.dtype)
        else:
            srcind=np.digitize(ju,self.cwav)-1

            
        # get the wavelength indices
        try:
            self.lam=ju-self.cwav[srcind]
        except:
            print(len(ju),len(srcind),len(sources))
            print('[debug]something wrong in matrix.py')
            import pdb
            pdb.set_trace()
            
        #self.lam=lam.astype(int)
        
        # get the reverse indices
        segids=np.array(list(sources.keys()))
        self.ri=indices.reverse(segids[srcind])
        self.hsrc=np.bincount(srcind.astype(int))

        # recast somethings
        aij=np.array(aij)
        
        # compute the frobenius norm
        self.frob=np.sqrt(np.sum(aij*aij))
        
        
        
        # sparse matrix is constructed as (ic,jc,np.array(mat['aij']),dim)
        self.A=ssl.aslinearoperator(coo_matrix((aij,(ic,jc)),shape=dim))
        del aij



        # record stuff
        self.bi=np.array(self.bi)
        self.icomp=ic
        self.iuniq=iu
        self.jcomp=jc
        self.juniq=ju
        
        # for making a plot
        self.lcurve=lcurve.LCurve(self.frob)

    #def epar2(self,src,conf,extconf,key):
    #    if getattr(src,key) is None:
    #        val=conf[key]
    #        if val is None:
    #            val=getattr(extconf,key)
    #        setattr(src,key,val)
    #        
    #        
    #def epar(self,conf,extconf,key):
    #    val=conf[key]
    #    if val is None:
    #        return getattr(extconf,key)
    #    else:
    #        return val

    def __len__(self):
        return len(self.A.A.data)
        
    def __imul__(self,v):
        self.A.A.data*=v
        self.frob*=v
        self.lcurve.frob*=v
        return self
    
        
    def loadFLT(self,flt,sources,extconf,mskconf,grismFF,pb,path):

        # output stuff
        i = []
        j = []
        aij = []
        
        # make mask for this FLT
        masks=self.maskBeams(flt,mskconf,path)
        import pickle,os,psutil      
        pid = os.getpid()
        py = psutil.Process(pid)
        # open the H5Table
        with h5table.H5Table(flt.dataset,self.TTYPE,path=path) as h5:
            if __RAM__:
                print("start loadFLT:",py.memory_info()[0]/1024/1024/1024)
            # loop over detectors
            for detname,detimg in flt:
                h5det=h5[detname]              # get the group
                detconf=extconf[detname]     # grism config

                # save this for easy access later
                self.npix=detimg.npix
                
                # read the images
                sci,scihdr=flt.readfits(detconf.sciext,detconf.extver)
                unc,unchdr=flt.readfits(detconf.uncext,detconf.extver)
                dqa,dqahdr=flt.readfits(detconf.dqaext,detconf.extver)
                xyg=[]         # a container

                # make a good pixel mask
                gpx=(dqa == 0) & (unc > 0)
                if len(masks)!=0:
                    gpx &= masks[detname]
                del dqa,dqahdr,unchdr      # don't need these anymore
                
                if __RAM__:
                    print("calling loadBeams:",py.memory_info()[0]/1024/1024/1024)
                # call a load beam
                data=self.loadBeams(h5det,detconf,detimg,unc,gpx,sources,\
                                    grismFF)
                self.imgindex+=1
                if __RAM__:
                    print("back from loadBeams:",py.memory_info()[0]/1024/1024/1024)

                # collect the results
                if len(data[3])!=0:
                    # collect the matrix terms
                    # i.extend(data[0])
                    # j.extend(data[1])
                    # aij.extend(data[2])

                    #i = np.hstack((i,data[0]))
                    #j = np.hstack((j,data[1]))
                    #aij = np.hstack((aij,data[2]))
                    i.append(data[0])
                    j.append(data[1])
                    aij.append(data[2])

                    # compute pixel (x,y) pairs
                    xyg=indices.unique(np.array(data[3]))

                    # the following line was encapsulated in unqiify
                    # (written by R Ryan), but needs to be explicitly
                    # put in for the differences with the way unique was
                    # implemented (could put sort flag in indices.unique)
                    xyg=np.sort(xyg)
                    
                    xg,yg=indices.one2two(xyg,detimg.naxis)
                    xg=xg.astype(int)
                    yg=yg.astype(int)
                    bi=sci[yg,xg]/unc[yg,xg]
                    del xg,yg     # clean up memory usage
                    
                    
                    # check for bad values in bi
                    g=np.where(np.isinf(bi))[0]
                    if len(g)!=0:
                        print('[warn]Infinite values in bi; is UNC image ok?')
                        print(bi[g])
                        raise RuntimeError("Infinite values. aborting.")

                    # like IDL's push
                    #self.bi.extend(bi)
                    self.bi = np.hstack((self.bi,bi))
                    del bi    # again, every little bit helps
                    
                # save the memory usage
                del data
        i = np.hstack(i)
        j = np.hstack(j)
        aij = np.hstack(aij)
        if __RAM__:
            print("done with loadBeams:",py.memory_info()[0]/1024/1024/1024)

        return i,j,aij
                
    def maskBeams(self,flt,mskconf,path):

        masks={}
        if len(mskconf.beams)!=0:
            print("[info]Making beam mask for: {}".format(flt.filename))
            with h5table.H5Table(flt.dataset,path=path,suffix='omt') as h5:
                
                # loop over detectors
                for detname,detimg in flt:
                    h5det=h5[detname]              # get the group
                    detconf=mskconf[detname]       # grism config
                    mask=np.ones(detimg.naxis,dtype=np.bool)
                    for beam,beamconf in detconf:

                        h5beam=h5det[beam]
                        for segid in h5beam:
                            xyg=h5beam[segid][:]
                            xg,yg=indices.one2two(xyg,detimg.naxis)
                            mask[yg,xg]=False
                    masks[detname]=mask
        return masks
    
    @property
    def segids(self):
        segids=[ri[0] for ri in self.ri]
        return segids
                
    def loadBeams(self,h5det,detconf,detimg,unc,gpx,sources,grismFF,\
                  thresh=-np.inf):
        thresh=np.float64(thresh)
        
        # output stuff
        #i,j,aij,xyg=np.array([],int),np.array([],int),np.array([],float),np.array([],int)
        i = []
        j = []
        aij = []
        xyg = []
        
        
        # loop over beams in question
        for beam,beamconf in detconf:
            h5beam=h5det[beam]
            
            # loop over the sources
            for srcindex,(segid,src) in enumerate(sources):

                if self.TTYPE=='ODT':                 # Read the ODT
                    odt=h5table.ODT(src.segid)
                    odt.readH5(h5beam)
                    ddt=odt.decimate()
                    del(odt)
                elif self.TTYPE=='DDT':               # Read the DDT
                    ddt=h5table.DDT(src.segid)
                    ddt.readH5(h5beam)
                else:
                    msg="Invalid Table Type: {}".format(self.TTYPE)
                    raise NotImplementedError(msg)

                if len(ddt)!=0:
                    
                    # get limits 
                    limits=src.limits
                    wav0=np.amin(limits)
                    wav1=np.amax(limits)
                    
                    # remove pixels out of range and/or in GPX
                    xg,yg=indices.one2two(ddt.xyg,detimg.naxis)
                    g=np.where((ddt.wav >=wav0) & (ddt.wav<=wav1) & \
                               (gpx[yg,xg]) & (ddt.val>thresh))[0]
                    if len(g)!=0:
                        # select the items that are good
                        ddt.select(g)
                        xg,yg=xg[g],yg[g]
                        del g
                                                
                        # compute the scaling terms
                        ff=grismFF(xg,yg,ddt.wav,detconf.detector)
                        pa=detimg.pixelArea(xg,yg)    # pixel area map
                        sens=beamconf.sensitivity(ddt.wav)*FLUXSCALE
                        
                        
                        # scale the DDT
                        ddt*=(ff*pa*sens)
                        del ff,pa,sens
                                                
                        # compute the wavelength indices
                        lamind=np.digitize(ddt.wav,limits)-1
                        
                        # scale the matrix elements by uncer
                        val=ddt.val/unc[yg,xg]
                        
                        # compute the matrix element
                        iii=ddt.xyg.astype(np.uint64)+\
                             self.imgindex*detimg.npix
                        jjj=lamind+self.cwav[srcindex]
                        ij=jjj+self.npar*iii
                        ij=ij.astype(np.uint64)
                        del iii,jjj
                        
                        # decimate over repeated indices
                        aiju,iju=indices.decimate(ij,val)
                        
                        # compute matrix coordinates
                        iu,ju=np.divmod(iju,self.npar)
                    
                        # compute pixel positions
                        imgind,xygind=np.divmod(iu,detimg.npix)

                        # downtype to save space
                        if self.downtype:
                            iu=iu.astype(np.uint32)
                            ju=ju.astype(np.uint32)
                            aiju=aiju.astype(np.float32)

                        
                        # save the matrix elements
                        # i.extend(list(iu))
                        # j.extend(list(ju))
                        # aij.extend(list(aiju))

                        #i = np.hstack((i,iu))
                        #j = np.hstack((j,ju))
                        #aij = np.hstack((aij,aiju))
                        i.append(iu)
                        j.append(ju)
                        aij.append(aiju)
                        del iu,aiju
                        
                        # compute the unique positions
                        #imgind=indices.unique(imgind)   # this is not needed
                        xygind=indices.unique(xygind)
                        #xyg.extend(list(xygind))
                        #xyg = np.hstack((xyg,xygind))
                        xyg.append(xygind)
                        del xygind
                                                
        i = np.hstack(i)
        j = np.hstack(j)
        aij = np.hstack(aij)
        xyg = np.hstack(xyg)
        return i,j,aij,xyg
                        

    def write(self,filename,filetype='ascii'):
        filetype=filetype.lower()

        if filetype=='ascii':
            with open(filename,'w') as f:
                for i,j,aij in zip(self.A.A.row,self.A.A.col,self.A.A.data):
                    print('{} {} {}'.format(i,j,aij),file=f)
        else:
            print('[warn]File type {} is unsupported.'.format(filetype))
            raise NotImplementedError("Invalid File type")
                
    def residualMatrix(self,j,resid):
        g=np.where((self.A.A.col == j))[0]
        
        if len(g)==0:
            print('[warn]No valid matrix elements for column={}'.format(j))
            return None,None
        
        ii=self.A.A.row[g]
        jj=self.A.A.col[g]
        aij=self.A.A.data[g]
        iic,iiu=indices.compress(ii)
        jjc,jju=indices.compress(jj)
 
        dim=np.array([max(iic),max(jjc)])+1

        
        A=ssl.aslinearoperator(coo_matrix((aij,(iic,jjc)),shape=dim))
        bi=resid[ii]
            
        return A,bi


    
    def runLSQR(self,logdamp,atol=None,btol=None,conlim=None,show=None,x0=None):

        if show is None: show=self.show
        if atol is None: atol=self.atol
        if btol is None: btol=self.btol
        if conlim is None: conlim=self.conlim
        
        logfrob=np.log10(self.frob)
        
        # force this to be a list
        if np.isscalar(logdamp):
            logdamp=[logdamp]

        # collect the outputs
        out=[]

        # iterate over logdamp... could Multiprocess this
        for ldamp in logdamp:
            t1=timeit.default_timer()
            if ldamp is None:
                damp=0.
            else:
                damp=np.power(10.,ldamp)*self.frob


                
                
            # run LSQR
            print("[info]Starting LSQR log(l) = {0:+.3f}".format(ldamp))
            
            '''
            # Using SciPy the way I think it works:
            r=ssl.lsqr(self.A,self.bi,damp=damp,x0=x0,show=show,calc_var=True,\
                       atol=atol,btol=btol,conlim=conlim,iter_lim=self.maxiter)


            '''
            
            # Using LSQR a la the IDL implementation
            if x0 is None:
                bi=self.bi
            else:
                bi=self.bi-self.A.matvec(x0)
            
            r=ssl.lsqr(self.A,bi,damp=damp,show=show,calc_var=True,\
                       atol=atol,btol=btol,conlim=conlim,iter_lim=self.maxiter)
            if x0 is not None:
                r=(r[0]+x0,*r[1:])


            # there doesn't seem to be any difference whatsoever.
                

            # get the final time
            t2=timeit.default_timer()
                
            # package the output
            r=lsqrresult.LSQRResult(*r,damp/self.frob,t2-t1)

            
            # update the plot
            self.lcurve.append(r.r1norm,r.xnorm,r.logdamp)

            # save the result
            out.append(r)
            
        if len(out)==1:
            out=out[0]


            
        return out

    

    @property
    def count(self):
        try:
            count=self.A.shape[0]*self.A.shape[1]
        except:
            count=0
        return count
    
    @property
    def shape(self):
        try:
            sh=self.A.shape
        except:
            sh=[None,None]
        return sh
        
    @property
    def norm(self):
        try:
            nrm=self.frob
        except:
            nrm=None
        return nrm
