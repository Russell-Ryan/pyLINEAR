from scipy import signal,optimize
from scipy.ndimage import convolve1d
import numpy as np
import pdb

from pylinear import h5table
from pylinear.utilities import indices,pool


class Model(object):
    def __init__(self,p0,form,table=None):        
        self.p0=p0
        self.npar=len(self.p0)
        if table is not None:
            assert (self.npar==1),'Invalid number of parameters'
            self.form='tabulated'
        else:
            self.form=form
    def __str__(self):
        return 'Cross dispersion profile model of {}'.format(self.form)
        
    def __call__(self,x,a):
        assert (len(a)==self.npar),'invalid number of parameters'

        if self.form =='polynomial':
            y=np.polyval(np.flip(a,0),x)
        elif self.form=='gaussian':
            z=(x-a[1])/a[2]
            y=a[0]/np.sqrt(2*np.pi)/a[2]*np.exp(-0.5*z*z)
        elif self.form=='tabulated':
            y=np.zeros_like(x,dtype=np.float)
            for i,v in zip(self.table['y'],self.table['v']):
                g=np.where(x==i)[0]
                if len(g)==1:
                    y[g]=a[0]*v
        else:
            pass

        return y
    


class Direct(object):
    def __init__(self):
        # parameters in the direct extraction
        self.skypars={'width':10,'order':2}
        self.coeffs=signal.savgol_coeffs(33,4,deriv=0,delta=1.0)

        
        self.fluxscale=1e-17       # just a number to avoid rounding errors

        # set up the models to fit
        self.models={}
        #self.models['source']=Model([1.],'tabulated',table=[])
        self.models['source']=Model(np.array([0,0,0.7]),'gaussian')
        self.models['sky']=Model(np.zeros(self.skypars['order']+1),'polynomial')

        

    def totModel(self,x,*a):
        y=np.zeros_like(x)
        i=0
        for name,model in self.models.items():
            j=i+model.npar
            y=y+model(x,a[i:j])
            i=j
        return y


    def fitSky(self,sci,unc,dqa,ddt):
        
        xg,yg=indices.one2two(ddt.xyg,sci.shape)

        y0=max(np.amin(yg)-self.skypars['width'],0)
        y1=min(np.amax(yg)+self.skypars['width'],sci.shape[1]-1)
        x0,x1=np.amin(xg),np.amax(xg)
        box=slice(y0,y1+1),slice(x0,x1+1)        

        sky=np.zeros([y1-y0+1,x1-x0+1])
        yy=np.arange(y0,y1+1)
        
        for j,xu in enumerate(indices.unique(xg)):
            y,f,u,g=self.crossDispersion(sci,unc,dqa,xg,yg,xu)


            if self.models['source'].form=='gaussian':
                w=np.absolute(f)
                yave=np.average(y,weights=w)
                ysig=np.sqrt(np.average((y-yave)**2,weights=w))

                self.models['source'].p0[0]=np.amax(f)
                self.models['source'].p0[1]=yave
                if ysig > 0.:
                    self.models['source'].p0[2]=ysig
            elif self.models['source'].form=='tabulated':
                v=np.array(ddt.val)[g]
                tabv,taby=indices.decimate(yg[g],v)
                tabv=tabv/np.sum(tabv)
                self.models['source'].table={'y':taby,'v':tabv}

                
            # update the initial conditions
            p0=[]
            for name,model in self.models.items():
                p0.extend(model.p0)

            # sometimes curve_fit fails, not sure why?
            try:
                p,pcov=optimize.curve_fit(self.totModel,y,f,sigma=u,p0=p0,\
                                          absolute_sigma=True)
            except:
                p=p0

            sky[:,j]=self.models['sky'](yy,p[-self.models['sky'].npar:])
            
        return sky,box

    def fitSource(self,sci,unc,dqa,ddt,beamconf):
        xg,yg=indices.one2two(ddt.xyg,sci.shape)

        # outputs
        flam,fvar,wave,chi2=[],[],[],[]


        skymod=self.models['sky']
        
        # remove the skymodel
        del self.models['sky']
        for xu in indices.unique(xg):
            y,f,u,g=self.crossDispersion(sci,unc,dqa,xg,yg,xu)

            # get moments of the cross dispersion
            w=np.absolute(f)
            yave=np.average(y,weights=w)
            ysig=np.sqrt(np.average((y-yave)**2,weights=w))
                        
            if self.models['source'].form=='gaussian':            
                # update the init
                self.models['source'].p0[0]=np.amax(f)
                self.models['source'].p0[1]=yave
                if ysig > 0.:
                    self.models['source'].p0[2]=ysig
                    
            elif self.models['source'].form=='tabulated':
                v=np.array(ddt.val)[g]
                tabv,taby=indices.decimate(yg[g],v)
                tabv=tabv/np.sum(tabv)
                self.models['source'].table={'y':taby,'v':tabv}


                    
            # update the initial conditions
            p0=[]
            for name,model in self.models.items():
                p0.extend(model.p0)
                
            # get wavelength values from DDT
            wav=np.array(ddt.wav)[g]
            val=np.array(ddt.val)[g]
            w=np.average(wav,weights=val)

            # sometimes curve_fit fails, not sure why?
            try:
                p,pcov=optimize.curve_fit(self.totModel,y,f,sigma=u,p0=p0,\
                                          absolute_sigma=True)
                r=(f-self.totModel(y,*p))/u
                
                # get grism corrections
                sens=beamconf.sensitivity(w)*self.fluxscale   # sensitivity
                disp=beamconf.dispersion(float(xu),yave)      # dispersion
                unit=disp*sens
                
                # apply the dispersion and sensitivity curve
                f=p[0]/unit
                v=pcov[0,0]/(unit*unit)
                
                # save the results
                flam.append(f)
                fvar.append(v)
                wave.append(w)
                chi2.append(np.sum(r*r))
            except:
                pass


        self.models['sky']=skymod
        return flam,fvar,wave,chi2

    
    def crossDispersion(self,sci,unc,dqa,xg,yg,xu):
        g=np.where(xg==xu)[0]
        y0=max(np.amin(yg[g])-self.skypars['width'],0)
        y1=min(np.amax(yg[g])+self.skypars['width'],sci.shape[1]-1)

        y=np.arange(y0,y1)
        s=sci[y0:y1,xu]
        u=unc[y0:y1,xu]
        d=dqa[y0:y1,xu]        
        gg=np.where(d==0)[0]
        if len(gg)==0:
            y,s,u=None,None,None
        else:
            y=y[gg]
            s=s[gg]
            u=u[gg]
        return y,s,u,g

    def cleanSky(self,img):
        new=[convolve1d(row,self.coeffs,mode='nearest') for row in img]
        return np.array(new)


    def getSpectrum(self,grism,extconf,path):

        fluxs,fvars,waves,chi2s=[],[],[],[]
        with h5table.H5Table(grism.dataset,'ddt',path=path) as h5:
            for detname,detimg in grism:
                # open the detector
                h5det=h5[detname]
                detconf=extconf[detname]
                
                # read the images
                sci,scihdr=grism.readfits(detconf.sciext,detconf.extver)
                unc,unchdr=grism.readfits(detconf.uncext,detconf.extver)
                dqa,dqahdr=grism.readfits(detconf.dqaext,detconf.extver)
                
                # load the beamsy
                for beam,beamconf in detconf:
                    h5beam=h5det[beam]
                    beamconf=detconf[beam]
                    
                    # read the table
                    ddt=h5table.DDT(self.segid)
                    ddt.readH5(h5beam)
                    
                    # apply flat, pam, etc. to sci/unc

                    
                    # fit the sky
                    sky,box=self.fitSky(sci,unc,dqa,ddt)
                                        
                    # clean the sky
                    cln=self.cleanSky(sky)
                    sci[box]-=cln
                    del cln,sky
                                        
                    # fit the object
                    vals=self.fitSource(sci,unc,dqa,ddt,beamconf)
                    
                    # clean up
                    del sci,unc,dqa
                    
                    # output the results
                    fluxs.extend(vals[0])
                    fvars.extend(vals[1])
                    waves.extend(vals[2])
                    chi2s.extend(vals[3])
                    del vals                     # more cleaning
                    
                    
        
        return fluxs,fvars,waves,chi2s

                    
    def directExtraction(self,grisms,extconf,conf):
        #flatten = lambda l: [item for sublist in l for item in sublist]

        path=conf['tables']['path']
        
        # load the spectra for each grism
        p=pool.Pool(self.getSpectrum,ncpu=conf['cpu']['ncpu'],
                    desc='direct extraction')
        results=p(grisms.values(),extconf,path)


        #p=pool.Pool(ncpu=conf['cpu']['ncpu'])
        #results=p(self.getSpectrum,grisms.values,extconf,path,\
        #          prefix='direct extraction')



        #results=[self.getSpectrum(g,extconf,conf) for n,g in grisms]
        
        # package the output
        fluxs,fvars,waves,chi2s=[],[],[],[]
        for r in results:
            fluxs.extend(r[0])
            fvars.extend(r[1])
            waves.extend(r[2])
            chi2s.extend(r[3])
            results.remove(r)
                                                
        # recast
        fluxs=np.array(fluxs)
        fvars=np.array(fvars)
        waves=np.array(waves)
        chi2s=np.array(chi2s)


        # outputs
        wave=np.arange(extconf.lamb0,extconf.lamb1+extconf.dlamb,extconf.dlamb)
        flam=np.full_like(wave,np.nan)
        func=np.full_like(wave,np.nan)

        # bin the data
        for j,wav in enumerate(wave):
            g=np.where((waves> wav-extconf.dlamb/2.) & \
                       (waves<=wav+extconf.dlamb/2.))[0]

            if len(g)!=0:
                w=1./fvars[g]
                f=fluxs[g]
                d=np.sum(w)
                flam[j]=(np.sum(w*f)/d)*self.fluxscale
                func[j]=(1./np.sqrt(d))*self.fluxscale

        #import matplotlib.pyplot as plt
        #plt.scatter(wave,flam/1e-17)
        #plt.show()
        
        return wave,flam,func



    
