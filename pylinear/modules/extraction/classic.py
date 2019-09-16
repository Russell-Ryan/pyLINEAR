from scipy import signal,optimize
import numpy as np
import pdb

from pylinear import h5table
from pylinear.utilities import indices
from .fluxunit import FLUXSCALE

''' Do classic "long slit-style" extraction '''


def fitSky(sci,unc,dqa,ddt,skyorder=2):
    sig0=0.7    # initial guess (in pix) (could get this from ddt?)
    
    
    
    xg,yg=indices.one2two(ddt.xyg,sci.shape)

    x0,x1=np.amin(xg),np.amax(xg)
    y0,y1=np.amin(yg),np.amax(yg)
    box=(x0,x1,y0,y1)
    sky=np.zeros([y1-y0+1,x1-x0+1])
    yy=np.arange(y0,y1+1)

    val=np.array(ddt.val)
    
    for j,xu in enumerate(indices.unique(xg)):
        y0,y1,g=boundingBox(xg,yg,xu,sci.shape)

        #yc=np.sum(val[g]*yg[g])/np.sum(val[g])
        #y2=np.sum(val[g]*yg[g]*yg[g])/np.sum(val[g])
        #sg=np.sqrt(y2-yc*yc)    # off by a factor 2.4 for GW17?
        #print(sg,sig0,sg/sig0)
        
        y,s,u=fittingData(y0,y1,xu,sci,unc,dqa)
        if y is None:
            print('bad value')
            q=input()

        # initial conditions
        opar=np.array([np.amax(s),(y1+y0)/2.,sig0])
        spar=np.zeros(skyorder+1)
        p0=np.concatenate((opar,spar))
        
        # call fitting routine
        try:
            p,pcov=optimize.curve_fit(model,y,s,sigma=u,p0=p0,\
                                      absolute_sigma=True)
            psky=p[3:]
        except:
            psky,pcov=optimize.curve_fit(skymodel,y,s,sigma=u,p0=spar,\
                                         absolute_sigma=True)
        sky[:,j]=skymodel(yy,*psky)
        #sky[:,j]=model(yy,*p)


    return box,sky
def skymodel(x,*a):
    sky=np.polyval(np.flip(a,0),x)
    return sky

def model(x,*a):
    
    z=(x-a[1])/a[2]
    obj=(a[0]/np.sqrt(2*np.pi)/a[2])*np.exp(-0.5*z*z)
    sky=np.polyval(np.flip(a[3:],0),x)
    return obj+sky


#def resid(a,y,s,w):
#    ''' return residuals '''
#    return (func(y,a)-s)*w
         


def fitSource(sci,unc,dqa,ddt,beamconf):
    sig0=0.6
    
    # output parameters
    flam,fvar,wave,par,dpar,chi2=[],[],[],[],[],[]

    xg,yg=indices.one2two(ddt.xyg,sci.shape)
    x=indices.unique(xg)
    for xu in x:
        y0,y1,g=boundingBox(xg,yg,xu,sci.shape)
        y,s,u=fittingData(y0,y1,xu,sci,unc,dqa)
        if y is None:
            print("bad value")
            q=input()
            
        opar=np.array([np.amax(s),(y1+y0)/2.,sig0])
        try:
            p,pcov=optimize.curve_fit(model,y,s,sigma=u,p0=opar,\
                                      absolute_sigma=True)
            
            # compute residual
            z=(s-model(y,*p))/u
            
            # wavelength values from DDT
            wav=np.array(ddt.wav)
            val=np.array(ddt.val)
            w=np.sum(wav[g]*val[g])/np.sum(val[g])
            
            # get grism properties
            sens=beamconf.sensitivity(w)*FLUXSCALE    # get sensitivity curve
            disp=beamconf.dispersion(float(xu),p[1])  # get dispersion
            unit=disp*sens

            # apply the dispersion and sensitivity curve
            f=p[0]/unit
            v=pcov[0,0]/(unit*unit)

            
            # average wavelength
            flam.append(f)
            fvar.append(v)
            wave.append(w)
            chi2.append(np.sum(z*z))
        except:
            pass
           
    return flam,fvar,wave,chi2

def fittingData(y0,y1,xu,sci,unc,dqa):
    y=np.arange(y1-y0)+y0
    
    s=sci[y0:y1,xu]
    u=unc[y0:y1,xu]
    #w=1./unc[y0:y1,xu]       # weights (for residual so not squared)
    d=dqa[y0:y1,xu]
    g=np.where(d == 0)[0]
    if len(g)!=0:
        y=y[g]
        s=s[g]
        u=u[g]

    else:
        y,s,u=None,None,None
    return y,s,u
        
def boundingBox(xg,yg,xu,dim,width=10):
    g=np.where(xg == xu)[0]
    miny=np.amin(yg[g])
    maxy=np.amax(yg[g])
    y0=max(miny-width,0)
    y1=min(maxy+width,dim[1]-1)
    return y0,y1,g
    

def cleanSky(img,width=33,degree=4):
    new=[signal.savgol_filter(row,width,degree,mode='nearest') for row in img]
    return np.array(new)

def extractOne(conf,source,grisms,extconf):

    wav0=extconf.lamb0
    wav1=extconf.lamb1
    dwav=extconf.dlamb

    
    fluxs,fvars,waves,chi2s=[],[],[],[]
    for dataset,grism in grisms:
        with h5table.H5Table(grism.dataset,'ddt',path=conf['path']) as h5:
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
                    ddt=h5table.DDT(source.segid)
                    ddt.readH5(h5beam)

                    # apply flat, pam, etc. to sci/unc
                    
                    # compute sky and remove it
                    (x0,x1,y0,y1),sky=fitSky(sci,unc,dqa,ddt)  # fit sky model
                    
                    
                    cln=cleanSky(sky)                    # clean the sky image

                    sci[y0:y1+1,x0:x1+1]-=cln            # subtract sky model
                                      
                    # fit the object
                    vals=fitSource(sci,unc,dqa,ddt,beamconf)

                    # save the results
                    fluxs.extend(vals[0])
                    fvars.extend(vals[1])
                    waves.extend(vals[2])
                    chi2s.extend(vals[3])

                    # clean up 
                    del vals,sci,unc,dqa,cln,sky

    # define output extraction grid
    wave=np.arange(wav0,wav1+dwav,dwav)
    flam=np.zeros_like(wave)
    func=np.zeros_like(wave)

    # retype for numpy
    waves=np.array(waves)
    fvars=np.array(fvars)
    fluxs=np.array(fluxs)

    # bin the data
    mode=conf['mode'].lower()
    for j,wav in enumerate(wave):

        g=np.where((waves > wav-dwav/2.) & (waves <= wav+dwav/2.))[0]
        if len(g)!=0:
            if mode=='inverr':          # inverse error weighting:
                w=1./fvars[g]           # define weights
                f=fluxs[g]              # data to average
                d=sum(w)                # a normalizing factor
                flam[j]=np.sum(w*f)/d
                func[j]=1/np.sqrt(d)
            else:
                pass
    import matplotlib.pyplot as plt
    plt.errorbar(wave,flam,yerr=func)
    plt.scatter(waves,fluxs,s=1)
    plt.xlim(wav0,wav1)
    plt.ylim(0,5)
    plt.show()

            
    return wave,flam,func
            
                    
def classicExtraction(sources,grisms,extconf):
    conf={'path':'TABLES2/','mode':'inverr'}
    for segid,source in sources:
        wave,flam,func=extractOne(conf,source,grisms,extconf)
        with open('{}.spc'.format(segid),'w') as fp:
            for w,f,u in zip(wave,flam,func):
                print(w,f,u,file=fp)


    print('done.')
    q=input()
