import os
from astropy.io import fits
import numpy as np
import polyclip
from timeit import default_timer
from .flatfield import UnityFlatField,ImageFlatField


class Spatial(object):
    def __init__(self,values):
        if np.isscalar(values):
            self.order=0
            self.coefs=[((0,0),values)]
        else:
            n=(np.sqrt(1+8*len(values))-1)/2
            N=int(n)
            assert(N>=n),'data must be a triangular number'
            
            powers=[(j-k,k) for j in range(N) for k in range(j+1)]
            self.coefs=list(zip(values,powers))
            self.order=N-1

    def __str__(self):
        return 'Spatial polynomial of order = {}'.format(self.order)
            
    def evaluate(self,xy):
        ''' evaluate the 2d polynomial at a scalar position (x,y) '''

        return sum(coef*xy[0]**i*xy[1]**j for coef,(i,j) in self.coefs)


class Parametric(object):
    def __init__(self,name):
        self.name=name
        self.polys=[]
        self.order=-1
        self.inverse_function=None


        
    def append(self,p):
        self.polys.append(p)
        self.order+=1

        if self.order==1:
            self.inverse_function=self._first
        elif self.order==2:
            self.inverse_function=self._second
        else:
            self.inverse_function=self._nth
            
            
    def _first(self,f,coefs):
        ''' analytically invert a 1st order polynomial '''
        return (f-coefs[0])/coefs[1]        

    def _second(self,f,coefs):
        ''' analytically invert a 2nd order polynomial '''
        raise NotImplementedError    

    def _nth(self,f,coefs):
        ''' numerically invert an arbitrary order polynomial '''
        raise NotImplementedError
    
    def __len__(self):
        ''' return the number of terms (N=order-1) '''
        return len(self.polys)

    def __str__(self):
        return "Parameteric polynomial of order = {}".format(self.order)   

    def coefs(self,xy,order=None):
        ''' compute the polynomial coeffs at some position (x,y) '''
        if order is None:
            coefs=[poly.evaluate(xy) for poly in self.polys]
        else:
            coefs=self.polys[order].evaluate(xy)
        return coefs    
        
    def evaluate(self,xy,t):
        ''' evaluate the polynomial at some position (x,y) and parameter '''

        f=sum(poly.evaluate(xy)*t**i for i,poly in enumerate(self.polys))
        return f

    def invert(self,xy,f):
        ''' invert the polynomial at some position (x,y) and function value '''

        #if self.inverse_function is None:
        #    print("ERROR!")
        #    print(self.polys)

            

        coefs=[poly.evaluate(xy) for poly in self.polys]
        t=self.inverse_function(f,coefs)
        return t
        
      
class Sensitivity(object):
    def __init__(self,sensfile,senslimit=1e14):
        self.sensfile=sensfile
        
        # read the file
        with fits.open(self.sensfile) as f:
            data=f[1].data
            
        # save the data
        self.sensitivity=data['SENSITIVITY']
        self.wavelength=data['WAVELENGTH']
        self.error=data['ERROR']
        
        # compute the range
        g=np.where(self.sensitivity > senslimit)
        self.wmin=np.amin(self.wavelength[g])
        self.wmax=np.amax(self.wavelength[g])

        # compute the max throughput
        self.smax=np.amax(self.sensitivity)

        
    def __mul__(self,a):
        self.sensitivity*=a
        self.error*=a
        self.smax*=a
        return self
        
    def __rmul__(self,a):
        return self.__mul__(a)
    
    def __call__(self,l,left=0.,right=0.):
        s=np.interp(l,self.wavelength,self.sensitivity,left=left,right=right)
        return s

    def __str__(self):
        return 'Sensitivity curve: {}'.format(self.sensfile)


class Beam(object):
    COMMENTS=['%','#','$','!']
    def __init__(self,conffile,beam):
        valid=lambda s: (len(s)>0 and not any(map(s.startswith,self.COMMENTS)))

        # record some stuff
        self.beam=beam
        self.conffile=os.path.join(os.environ['PYLINEAR_CONFIG'],conffile)

        print('[debug]Look into wedge offsets')

        # the three main functions
        self.dispx=Parametric('dispx')
        self.dispy=Parametric('dispy')
        self.displ=Parametric('displ')

        # define the local path
        path=os.path.dirname(self.conffile)

        # open the file
        with open(self.conffile,'r') as fp:
            for line in fp:
                line=line.strip()
                if valid(line):
                    tokens=line.split(' ')
                    key=tokens[0].upper()
                    val=tokens[1:]

                    if key.startswith('FFNAME'):
                        self.ffname=os.path.join(path,val[0])
                        
                    if key.startswith('XRANGE_{}'.format(beam)):
                        self.xr=np.array(val[0:2],dtype=np.float32)

                    if key.startswith('YRANGE_{}'.format(beam)):
                        self.yr=np.array(val[0:2],dtype=np.float32)
                        
                    if key.startswith('DISPX_{}'.format(beam)):
                        val=[self.fix_type(v) for v in val if valid(v)]
                        self.dispx.append(Spatial(val))

                    if key.startswith('DISPY_{}'.format(beam)):
                        val=[self.fix_type(v) for v in val if valid(v)]
                        self.dispy.append(Spatial(val))

                    if key.startswith('DISPL_{}'.format(beam)):
                        val=[self.fix_type(v) for v in val if valid(v)]
                        self.displ.append(Spatial(val))

                    if key.startswith('NAXIS'):
                        self.naxis=np.array(val[0:2],dtype=np.uint16)
                        
                    if key.startswith('SENSITIVITY_{}'.format(beam)):
                        sensfile=os.path.join(path,val[0])
                        self.sensitivity=Sensitivity(sensfile)

                        
        # get a polygon clipper
        self.polyclip=polyclip.Polyclip(self.naxis)


        # just some quick error checking
        okay=(len(self.dispx)>0 and len(self.dispy)>0 and len(self.displ)>0)
        assert okay,'{} order is not present in the config file.'.format(beam)

        
    def __str__(self):
        return "Grism beam for {}".format(self.beam)
        
    def fix_type(self,v):
        try:
            v=int(v)
        except ValueError:
            try:
                v=float(v)
            except ValueError:
                pass
        return v

    def load_flatfield(self,unity=False):
        if unity or not hasattr(self,'ffname'):
            ff=UnityFlatField(np.flip(self.naxis))
        else:
            ff=ImageFlatField(self.ffname)            
        return ff
    
    def dispersion(self,xy):
        dxdt=self.dispx.coefs(xy,order=1)
        dydt=self.dispy.coefs(xy,order=1)
        dldt=self.displ.coefs(xy,order=1)
        drdt=np.sqrt(dxdt*dxdt+dydt*dydt)
        return dldt/drdt

    
    def wavelengths(self,xc,yc,nsub):
        disp=self.dispersion((xc,yc))/nsub
        delta=self.sensitivity.wmax-self.sensitivity.wmin

        #w0=np.arange(self.sensitivity.wmin,self.sensitivity.wmax+disp,disp)
        
        nwave=int(delta/disp)+2
        dwave=delta/(nwave-1.)
        
        wave=np.arange(nwave)*dwave+self.sensitivity.wmin
        
        return wave


    def disperse(self,xd,yd,wav):
        nx=len(xd)
        nw=len(wav)
        xg=np.empty((nw,nx))
        yg=np.empty((nw,nx))
        for i,xyd in enumerate(zip(xd,yd)):
            t=self.displ.invert(xyd,wav)
            xg[:,i]=self.dispx.evaluate(xyd,t)+xyd[0]
            yg[:,i]=self.dispy.evaluate(xyd,t)+xyd[1]
        return xg,yg

    def drizzle(self,xd,yd,wav,ignore='average',pixfrac=1.):
        assert (np.abs(pixfrac-1.)<=1e-3),'pixfrac must be 1'

        # apply the ignoring procedure
        if hasattr(self,'xr') and hasattr(self,'yr'):
            ignore=ignore.lower()
            if ignore=='average':
                # if average of pixel is in bounding box
                xave=np.average(xd)
                yave=np.average(yd)
                if (xave<self.xr[0]) or (xave>self.xr[1]) or \
                   (yave<self.yr[0]) or (yave>self.yr[1]):
                    return [],[],[],[]
            elif ignore=='minmax':
                # test min/max in range
                x0,x1=np.amin(xd),np.amax(xd)
                y0,y1=np.amin(yd),np.amax(yd) 
                if (x1<self.xr[0]) or (x0>self.xr[1]) or \
                   (y1<self.yr[0]) or (y0>self.yr[1]):
                    return [],[],[],[]
            else:
                pass
        
        # disperse each polygon vertix
        xg,yg=self.disperse(xd,yd,wav)

        # apply clipping
        xg=np.clip(xg,0,self.naxis[0])
        yg=np.clip(yg,0,self.naxis[1])
        
        # clip against a pixel grid
        x,y,area,indices=self.polyclip(xg,yg)

        # replicate the wavelength indices
        n=len(x)
        if n>0:
            i0=indices[0:-1]
            i1=indices[1:]
            gg=np.where(i1 != i0)[0]
            lam=np.empty(n,dtype=np.uint16)
            for g,a,b in zip(gg,i0[gg],i1[gg]):
                lam[a:b]=g
        else:
            lam=[]

                
        #tab=[]
        #xx,yy,ll,aa=[],[],[],[]
        #if len(x)!=0:
        #    for l,w in enumerate(wav):
        #       j0,j1=indices[l],indices[l+1]
        #        
        #        if j1>j0:
        #            xx.extend(x[j0:j1])
        #            yy.extend(y[j0:j1])
        #            ll.extend([l]*(j1-j0))
        #            aa.extend(area[j0:j1])
        #return x,y,lam,area

        return x,y,lam,area


    def sensitivity(self,wav,**kwargs):
        return self.sens(wav,**kwargs)
    
   
if __name__=='__main__':
    beam=Beam('/Users/rryan/Python/Russell-Ryan/pylinear/pylinear2/grism/calibrations/HST/WFC3/IR/IR/G102/g102.conf','+1')
    beam=Beam('/Users/rryan/Python/Russell-Ryan/pylinear/pylinear2/grism/calibrations/JWST/NIRISS/NIRISS_F090W_GR150C.conf','+1')

    ff=beam.load_flatfield()
    
    xg=np.array([905,905,906,906],dtype=np.float)
    #xg=np.array([150,150,151,151],dtype=np.float)
    #xg=np.array([-150,-150,-149,-149],dtype=np.float)
    xg=np.array([-1000,-1000,-999,-999],dtype=np.float)
    yg=np.array([51,52,52,51],dtype=np.float)
    wave=np.arange(9000.,10005.,5.)
    p=beam.drizzle(xg,yg,wave)
    print(p)
    #x,y,l,a=zip(*p)
    
