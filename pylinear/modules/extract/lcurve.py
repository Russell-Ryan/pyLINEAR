import matplotlib.pyplot as plt
import matplotlib.colors as mc
from matplotlib.backends.backend_pdf import PdfPages
import datetime
import numpy as np
from astropy.table import Table

from .menger import menger    # to compute Menger curvature

class LCurve(object):
    def __init__(self,norm=None):
        self.x=[]       # = log(r1norm) (r1norm is like chi2)
        self.y=[]       # = log(xnorm) (||f||)
        self.l=[]       # = log(damp)
        self.norm=norm
        
        
    def __len__(self):
        return len(self.x)

    def clear(self):
        self.x.clear()
        self.y.clear()
        self.l.clear()
    
    def append(self,x,y,l):
        self.x.append(np.log10(x))
        self.y.append(np.log10(y))
        self.l.append(l)

    def values(self,sort='x'):
        x=np.array(self.x)
        y=np.array(self.y)
        l=np.array(self.l)
        if sort is not None:
            i=np.argsort(x)
            x=x[i]
            y=y[i]
            l=l[i]
        else:
            i=np.np.arange(len(self))
            
        return x,y,l,i

    
    def compute_curvature(self):
        x,y,l,i=self.values()

        curv=np.full_like(x,np.nan,dtype=np.float)
        for j in range(1,len(x)-1):
            i,k=j-1,j+1
            curv[j]=menger((x[i],y[i]),(x[j],y[j]),(x[k],y[k]))
            #kurv=vector(x,y)

        #for c,k in zip(curv,kurv):
        #    print(c,k,c-k)
        
            
        return curv


    

    def plot(self,arg,**kwargs):
        if isinstance(arg,str):
            with PdfPages(arg) as pdf:
                self.write_pdf(pdf,**kwargs)
        elif isinstance(arg,PdfPages):
            self.write_pdf(arg,**kwargs)
        else:
            raise NotImplementedError("Invalid plot input")

    
    def write_products(self,fileroot):
        self.write_ascii('{}_lcv.dat'.format(fileroot))
        self.plot('{}_lcv.pdf'.format(fileroot))

    
    def write_ascii(self,filename):
        now=datetime.datetime.now()
        date=now.strftime("%Y-%m-%d")

        x,y,l,i=self.values()
        c=self.compute_curvature()
        
        with open(filename,'w') as fp:
            print('# File written by pyLINEAR: {}'.format(date),file=fp)
            print('# 1: iteration',file=fp)
            print('# 2: log(ell)',file=fp)
            print('# 3: log(||Ax-b||^2)',file=fp)
            print('# 4: log(||x||^2)',file=fp)
            print('# 5: curvature',file=fp)
            for v in zip(i,l,x,y,c):
                print('{0} {1:+.4f} {2:+.8e} {3:+.8e} {4:+.8e}'.format(*v),
                      file=fp)

    @classmethod
    def load_ascii(cls,filename):
        obj=cls()
        names=('l','x','y','c')
        data=Table.read(filename,format='ascii.no_header',names=names)
        obj.x=list(data['x'])
        obj.y=list(data['y'])
        obj.l=list(data['l'])
        return obj
        
                

    def write_pdf(self,pdf,colormap='Spectral',grpid=None):
          # define a colormap
        cmap=plt.cm.get_cmap(colormap)

        # lighten the colormap
        cmap=self.cmap_map(lambda x: 0.5*(1.+x),cmap)
        
        # get the data 
        x,y,l,i=self.values()
        curv=self.compute_curvature()
        
        xt,yt=0.67,0.88


        gridspec_kw={'height_ratios':[0.8,1]}
        fig,(ax1,ax2)=plt.subplots(2,1,sharex=False,\
                                   gridspec_kw=gridspec_kw)

        if grpid is not None:
            ax1.set_title('group: {}'.format(grpid))
        
        ln=ax1.plot(x,y,'-k',linewidth=1.,zorder=1)
        sc=ax1.scatter(x,y,c=l,zorder=2,\
                       vmin=np.amin(l),vmax=np.amax(l),\
                       s=40,cmap=cmap,\
                       edgecolors='k',marker='o')

        if self.norm is not None:
            tt=ax1.text(xt,yt,r'$\log\ ||A||_F=${0:+.3f}'.format(self.norm),\
                        horizontalalignment='left',transform=ax1.transAxes,\
                        bbox=dict(facecolor='white',edgecolor='white'))
        
        ax1.set(xlabel=r'$\log\ ||Ax-b||^2$',\
                ylabel=r'$\log\ ||x||^2$')
        
        
        ax1.set_axisbelow(True)
        ax1.grid(True)
        
        
        l0,l1=np.amin(l),np.amax(l)
        if l0==l1:
            l0-=0.5
            l1+=0.5
        
        ln=ax2.plot(l,curv,'-k',linewidth=1.,zorder=1)
        #ln=ax2.semilogy(l,curv,'-k',linewidth=1.,zorder=1)
        
        
        sc=ax2.scatter(l,curv,c=l,zorder=3,\
                       vmin=np.amin(l),vmax=np.amax(l),\
                       s=40,cmap=cmap,\
                       edgecolors='k',marker='o')

        if len(curv)>1:
            g=np.where(curv == np.nanmax(curv))[0][0]
        else:
            g=0
        loglmax=l[g]

        ax2.axvline(x=loglmax,color='k',linestyle=':',zorder=2)
            
        ax2.set(ylabel=r'curvature')
        ax2.set_xticklabels([])

        
        ax2.set_xlim([l0,l1])
        ax2.set_axisbelow(True)
        
        ax2.grid(True)
        
        cbar=plt.colorbar(sc,ax=ax2,orientation='horizontal',pad=0.0,\
                          aspect=60,shrink=1)
        cbar.ax.set_xlabel(r"$\log\ \ell$")
        
        
        plt.tight_layout()
        pdf.savefig(fig)
        plt.close()
        



    @staticmethod
    def cmap_map(function,cmap):
        """ Applies function (which should operate on vectors of shape 3: [r, g, b]), on colormap cmap.
        This routine will break any discontinuous points in a colormap.
        """
        cdict = cmap._segmentdata
        step_dict = {}
        # Firt get the list of points where the segments start or end
        for key in ('red', 'green', 'blue'):
            step_dict[key] = list(map(lambda x: x[0], cdict[key]))
        step_list = sum(step_dict.values(), [])
        step_list = np.array(list(set(step_list)))
        # Then compute the LUT, and apply the function to the LUT
        reduced_cmap = lambda step : np.array(cmap(step)[0:3])
        old_LUT = np.array(list(map(reduced_cmap, step_list)))
        new_LUT = np.array(list(map(function, old_LUT)))
        # Now try to make a minimal segment definition of the new LUT
        cdict = {}
        for i, key in enumerate(['red','green','blue']):
            this_cdict = {}
            for j, step in enumerate(step_list):
                if step in step_dict[key]:
                    this_cdict[step] = new_LUT[j, i]
                elif new_LUT[j,i] != old_LUT[j, i]:
                    this_cdict[step] = new_LUT[j, i]
            colorvector = list(map(lambda x: x + (x[1], ), this_cdict.items()))
            colorvector.sort()
            cdict[key] = colorvector

        return mc.LinearSegmentedColormap('colormap',cdict,1024)
            



if __name__=='__main__':
    x=LCurve.load_ascii('test_lcv.dat')
    x.plot('test_lcv')
