import os
from astropy.io import fits
import numpy as np
from timeit import default_timer
import h5py


from .. import header_utils
from .menger import menger
from .matrix import Matrix
from .fluxunit import FLUXSCALE,FLUXUNIT
from .mcmc import MCMC
from .result import Result

class Extract(object):
    PHI=(1.+np.sqrt(5.))/2.    # DEFINE THE GOLDEN RATIO

    def __init__(self,path='tables',inverter='lsqr',method='golden',**kwargs):
                 
        self.path=os.path.join(path)

        self.inverter=inverter
        if not os.path.isdir(self.path):
            os.mkdir(self.path)

        self.method=method
        
        self.mcmc=MCMC(**kwargs)


    def open_hdf5(self,hdf5file,mode):
        self.hdf5file=hdf5file
        self.h5=h5py.File(self.hdf5file,mode)
            
    def __del__(self):
        self.close()

    def close_hdf5(self):
        if hasattr(self,'h5'):
            self.h5.close()

        
    @property
    def method(self):
        return self.algorithm
    
    @method.setter
    def method(self,method):
        method=method.lower()
        if method=='golden':
            self.algorithm=method
            self._method=self.golden_search
        elif method=='grid':
            self.algorithm=method
            self._method=self.grid_search
        elif method=='single':
            self.algorithm=method
            self._method=self.single_step
        else:
            raise NotImplementedError("method is not valid")


    def get_damping_target(self):
        print('[info]Building a damping target')

        targ=np.zeros(self.matrix.npar,dtype=np.float)
        #indices=[i for i,ri in self.matrix.ri]
        for source in self.sources:

            if source.segid in self.matrix.ri:
            
            #if source.segid in indices:
                #index=indices.index(source.segid)
                #s,g1=self.matrix.ri[index]
                #if s==source.segid:
                g1=self.matrix.ri[source.segid]
                g2=self.matrix.lam[g1]
                waves=source.wavelengths()
                targ[g1]=source.sed.interpolate(waves[g2])/FLUXSCALE

        return targ


    def load_matrix_hdf5(self,sources,group=0):
        if hasattr(self,'h5'):
            self.sources=sources
            self.optimized=False
            self.matrix=Matrix.from_hdf5(self.h5,group)
            if not self.matrix:
                # do a quick test that segids match
                if not all(s.segid in self.matrix.segids for s in self.sources):
                    print('[warn]Incompatible SEGIDs in matrix file.')
            else:
                print('[warn]Matrix could not be loaded.')


            
    def load_matrix_file(self,grisms,sources,beams,path,group=0,
                         mskbeams=None,target=True):


        self.sources=sources
        self.optimized=False     # set a default value
        
        # build the matrix into the self
        self.matrix=Matrix(grisms,sources,beams,path=path,mskbeams=mskbeams,
                           group=group,inverter=self.inverter)
        if len(self.matrix)==0:
            print('[alarm]Matrix has no elements. Cannot set damping target.')
            return
        
        # apply a damping target
        if target:
            target_spectra=self.get_damping_target()
            self.matrix.set_damping_target(target_spectra)


        # save the matrix if
        if hasattr(self,'h5'):
            self.matrix.to_hdf5(self.h5)
        
            
    def golden_search(self,logdamp):
        assert(len(logdamp)==3),'Golden Search requires a 3-element list'
        self.optimized=True
        
        # interpret some the inputs:
        # x1,x4 are initial conditions, eps is convergence tolerance
        x1,x4,eps=logdamp[0],logdamp[1],logdamp[2]
        x2=(x4+self.PHI*x1)/(1+self.PHI)
        x3=x1+(x4-x2)
        state=[self.matrix.invert(x) for x in (x1,x2,x3,x4)]
        
    
        # start the Cultrera algorithm
        while (state[3].damp-state[0].damp)>eps*state[3].damp:

            # compute curvatures
            c2=menger(state[0].xy,state[1].xy,state[2].xy)
            c3=menger(state[1].xy,state[2].xy,state[3].xy)
            
            # make sure the c3 curvature is positive
            while c3<0:

                # swap states
                state[3]=state[2]
                state[2]=state[1]
                
                # select a new damping value and compute a new state
                x2=(state[3].logdamp+self.PHI*state[0].logdamp)/(1+self.PHI)
                state[1]=self.matrix.invert(x2)
                
                # compute new curvature
                c3=menger(state[1].xy,state[2].xy,state[3].xy)


            # now update the optimized value
            if c2>c3:
                opt=state[1]     # optimal solution
                
                # swap the states
                state[3]=state[2]
                state[2]=state[1]
                
                # compute new damping and state
                x2=(state[3].logdamp+self.PHI*state[0].logdamp)/(1+self.PHI)
                state[1]=self.matrix.invert(x2)
                
            else:
                opt=state[2]     # optimal solution
                
                # swap the states
                state[0]=state[1]
                state[1]=state[2]
                
                # compute new damping and state
                x3=state[0].logdamp+(state[3].logdamp-state[1].logdamp)
                state[2]=self.matrix.invert(x3)
                
                
        # return the optimal value
        return opt


    
    def grid_search(self,logdamp):

        assert(len(logdamp)==3),'Grid Search requires a 3-element list'
        self.optimized=True

        # this is a very simplistic implementation of the grid search.
        # in truth, we do not need to keep the results at every step, but
        # rather we really only need 3 states and 1 optimized result
        # and compute the maximum on-the-fly.  I will code this up when
        # it is needed.

        # compute a grid of log damping
        logdamp = np.arange(logdamp[0],logdamp[1]+logdamp[2],logdamp[2])

        # get the states
        states=[self.matrix.invert(ld) for ld in logdamp]

        # compute the curvature
        curv=np.full_like(logdamp,np.nan)
        for i in range(1,len(curv)-1):
            curv[i]=menger(states[i-1].xy,states[i].xy,states[i+1].xy)


        # find the max
        i=np.nanargmax(curv)

        
        '''
        # initialize the states
        state1=self.matrix.invert(logdamp[0])
        state2=self.matrix.invert(logdamp[1])
        state3=self.matrix.invert(logdamp[2])
        
        curv=menger(state1.xy,state2.xy,state3.xy)
        opt=state2
        for ld in logdamp[3:]:
            state1=state2
            state2=state3
            state3=self.matrix.invert(ld)
            c=menger(state1.xy,state2.xy,state3.xy)

            if c>curv:
                curv=c
                opt=state2
        '''
        return states[i]


    def single_step(self,logdamp):
        self.optimized=False

        if isinstance(logdamp,(list,tuple,np.ndarray)):
            logdamp=logdamp[0]

        return self.matrix.invert(logdamp) 

   
    def run(self,logdamp,pdf=None,mcmc=False,residuals=None):

        t1=default_timer()


        # make the flux unit variable for outputting
        fluxunit='{} {}'.format(FLUXSCALE,FLUXUNIT)




        if len(self.matrix)>0:
        
            # iteratively call LSQR to maximize the curvature
            res=self._method(logdamp)

            # compute model and update residuals
            if residuals is not None:
                residuals.update_model(self.matrix,res.x)


            # simple uncertainty propagation
            #for j,xj in enumerate(res.x):
               # this should give the smae results as the MCMC, but here I've
               # done the calculus to show the MCMC result.  If consider a
               # single point (x_j), and don't do regularization,
               # chi2 = sum_i(Ai*x-bi)^2
               # dchi2/dx = 2 sum_i (Ai*x-bi)*Ai = 0
               # sum(Ai^2)*x = sum(Ai*bi)
               # x = sum(Ai*bi)/sum(Ai*Ai)
               # now do propagation of errors, but recall that sigma_i^2
               # should be in the den of all terms above.  then get
               # dx = 1/sqrt(sum_i (A_i/sigma_i)^2)
               #
               # this gives very good approximation of the MCMC result.
               # this should be the same as computing the diagonal elements
               # to the matrix representation for (AT*A)_ii.  But we do this
               # in the loop because AT*A is not necessarily sparse and
               # can require too much memory.
               #
               # the original MCMC approach is still valid, as it will provide
               # asymmetric error bars, which is probably better at low fluxes
               
               #print('[debug]Update simple error estimate')
               #mat,bi=self.matrix.sub_matrix(j,res.x)
               #tot=np.sum(mat.A.data*mat.A.data)
               #res.lo[j]=res.hi[j]=1./np.sqrt(tot)
            #pass

            # Do the analytic uncertainty propagation
            unc=self.matrix.estimate_uncertainty()
            if len(unc)!=len(res.lo):
                print('[warn]Un-fixable error in computing uncertainty')
            res.lo=np.copy(unc)
            res.hi=np.copy(unc)

        
            
            # if making a plot:
            if pdf is not None:
                self.matrix.lcurve.write_pdf(pdf)
            
            # do the MCMC simulation
            if mcmc:
                unc=self.mcmc.run(self.matrix,res)

        
            # get indices to unpack matrix below (this shoudl really be in
            # matrix) this is because they are sorted in ri
            #indices=[i for i,ri in self.matrix.ri]

        else:
            # invalid matrix.  making dummy data
            res=Result("None. Invalid matrix.")
            
        # package the outputs
        hdus={}
        for source in self.sources:
            
            # define the default output for the source
            wave=source.wavelengths()
            flam=np.full_like(wave,np.nan)
            flo=np.full_like(wave,np.nan)
            fhi=np.full_like(wave,np.nan)
                                    
            # parse the matrix to get the spectrum for each source
            if len(self.matrix)>0:# and source.segid in self.matrix.segids:

                # original thing sseemed to break with 2d flux cube. not sure?
                #index=self.matrix.segids.index(source.segid)
                #s,g1=self.matrix.ri[index]

                if source.segid in self.matrix.ri:
                # new thing requires an auxillary variable (indices)
                #if source.segid in indices:
                    #index=indices.index(source.segid)
                    #s,g1=self.matrix.ri[index]
                    
                    #if s==source.segid:
                    g1=self.matrix.ri[source.segid]
                    if len(g1)!=0:
                        g2=self.matrix.lam[g1]
                        flam[g2]=res.x[g1]
                        flo[g2]=res.lo[g1]
                        fhi[g2]=res.hi[g1]
                else:
                    print('[warn]{} was not measured.'.format(source.segid))
            else:
                print('[alarm]Matrix has no elements.')

                    
            # make the FITS table columns
            col1=fits.Column(name='wavelength',format='1D',unit='A',array=wave)
            col2=fits.Column(name='flam',format='1D',unit=fluxunit,array=flam)
            col3=fits.Column(name='flounc',format='1D',unit=fluxunit,array=flo)
            col4=fits.Column(name='fhiunc',format='1D',unit=fluxunit,array=fhi)
            cols=fits.ColDefs([col1,col2,col3,col4])

            # package into a fits object
            hdu=fits.BinTableHDU.from_columns(cols)

            # update the header of the FITS table
            hdu.header.set('EXTNAME',value='SOURCE',after='TUNIT4',
                           comment='extension name')
            hdu.header.set('EXTVER',value=source.segid,after='EXTNAME',
                           comment='extension version')

            # put the source content in the header
            source.update_header(hdu.header,group=self.matrix.group)


            # update header with MCMC
            self.mcmc.update_header(hdu.header)

            # this coudl go in MCMC
            #hdu.header.set('MCMC',value=mcmc,after='GROUP',
            #               comment='was MCMC simulation performed')
            #hdu.header.set('SAMPLER',value=self.mcmc.sampler,after='MCMC',
            #               comment='MCMC sampler used')
            #hdu.header.set('NWALKER',value=self.mcmc.nwalker,after='SAMPLER',
            #               comment='number of walkers')
            #hdu.header.set('NSTEP',value=self.mcmc.nstep,after='NWALKER',
            #               comment='number of steps per walker')
            #hdu.header.set('NSAMPLE',value=self.mcmc.nsample,after='NSTEP',
            #               comment='number of samples from posterior')
            #hdu.header.set('BURNFRAC',value=self.mcmc.burnfrac,after='NSAMPLE',
            #               comment='fraction of steps to burn')            
            #hdu.header.set('',value='',after='GROUP')
            #hdu.header.set('',value='      / MCMC Settings',after='GROUP')
            #hdu.header.set('',value='',after='GROUP')

            
            # record the HDU in the output dictionary
            hdus[source.segid]=hdu
            
        #set the group data
        if len(self.matrix)>0:
            x,y,l,i=self.matrix.lcurve.values()
            c=self.matrix.lcurve.compute_curvature()
        else:
            # an empty matrix.  so make dummy data
            x=np.array([])
            y=np.array([])
            l=np.array([])
            c=np.array([])
        # make the fits table columns
        col1=fits.Column(name='logdamp',format='1D',array=l)
        col2=fits.Column(name='logr1norm',format='1D',array=x)
        col3=fits.Column(name='logxnorm',format='1D',array=y)
        col4=fits.Column(name='curvature',format='1D',array=c)
        cols=fits.ColDefs([col1,col2,col3,col4])

        # package the data into a fits table
        hdu=fits.BinTableHDU.from_columns(cols)

        # update the group header
        hdu.header.set('EXTNAME',value='GROUP',after='TFORM4',
                       comment='extension name')
        hdu.header.set('EXTVER',value=self.matrix.group,after='EXTNAME',
                       comment='extension version')

        # update header for the matrix
        self.matrix.update_header(hdu.header)

        # put the results from the Minimizer
        res.update_header(hdu.header)
        *_,last=hdu.header.keys()    # get the last keyword

        # put some stuff about this run        
        hdu.header.set('METHOD',value=self.method,after=last,
                       comment='method to run LSQR')
        hdu.header.set('OPTIMIZE',value=self.optimized,after='METHOD',
                       comment='was curvature optimized')
        hdu.header.set('LOGDAMP',value=res.logdamp,after='OPTIMIZE',
                       comment='log(damping parameter) unscaled')

        try:
            nlcurve=len(self.matrix.lcurve)
        except:
            nlcurve=0
        hdu.header.set('NLCURVE',value=nlcurve,after='LOGDAMP',
                       comment='number of L-curve steps')
        header_utils.add_stanza(hdu.header,'L-Curve Results',before='METHOD')
    
        return hdus,hdu    

