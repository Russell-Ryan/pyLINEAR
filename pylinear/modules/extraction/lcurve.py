import matplotlib.pyplot as plt
import matplotlib.colors as mc
from matplotlib.backends.backend_pdf import PdfPages
import colorsys
import numpy as np
import datetime

from .methods import menger


''' Class to make a diagnostic LCurve plot for LINEAR '''

class LCurve(object):
    def __init__(self,frob):
        self.x=[]
        self.y=[]
        self.l=[]
        self.frob=frob
        
    def append(self,x,y,l):
        self.x.append(np.log10(x))
        self.y.append(np.log10(y))
        self.l.append(l)

    def values(self):
        x=np.array(self.x)
        y=np.array(self.y)
        l=np.array(self.l)
        i=np.argsort(x)
        
        return x[i],y[i],l[i]

    def load(self,filename,comments=['#','%',';']):
        with open(filename,'r') as fp:
            for line in fp:
                line=line.strip()
                if line[0] not in comments:
                    tokens=line.split(' ')
                    tokens=[float(token) for token in tokens if token!='']
                    if len(tokens)==3:
                        self.x.append(tokens[0])
                        self.y.append(tokens[1])
                        self.l.append(tokens[2])
                    
                        

        
    def write(self,filename):
        now=datetime.datetime.now()
        date=now.strftime("%Y-%m-%d")

        x,y,l=self.values()
        c=self.curvature
        
        with open(filename,'w') as fp:
            print('# File written by pyLINEAR: {}'.format(date),file=fp)
            print('# 1: log(ell)',file=fp)
            print('# 2: log(||Ax-b||^2)',file=fp)
            print('# 3: log(||x||^2)',file=fp)
            print('# 4: curvature',file=fp)
            print('',file=fp)
            
            for xx,yy,ll,cc in zip(l,x,y,c):
                print('{0:+.4f} {1:+.4e} {2:+.4e} {3:+.4e}'.format(xx,yy,ll,cc),file=fp)
                



    
    def cmap_map(self,function, cmap):
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
            
    @property
    def curvature(self):
        x,y,l=self.values()
        
        # compute the curvature
        curv=np.full_like(x,np.nan,dtype=np.float)
        for i in range(len(x)-2):
            jj,kk,ll=i,i+1,i+2
            curv[kk]=menger((x[jj],y[jj]),(x[kk],y[kk]),(x[ll],y[ll]))

        return curv

    
    def plot(self,filename,fontsize=14,colormap='Spectral'):

        
        # define a colormap
        cmap=plt.cm.get_cmap(colormap)

        # lighten the colormap
        cmap=self.cmap_map(lambda x: 0.5*(1.+x),cmap)
        
        # get the data 
        x,y,l=self.values()
        curv=self.curvature
        
        xt,yt=0.67,0.93
            

        with PdfPages(filename) as pdf:

            # make L-curve figure        
            fig,ax=plt.subplots()

            ln=ax.plot(x,y,'-k',linewidth=1.,zorder=1)
            sc=ax.scatter(x,y,c=l,zorder=2,\
                          vmin=np.amin(l),vmax=np.amax(l),\
                          s=40,cmap=cmap,\
                          edgecolors='k',marker='o')
            tt=ax.text(xt,yt,r'$\log\ ||A||_F=${0:+.3f}'.format(self.logfrob),\
                       horizontalalignment='left',transform=ax.transAxes,\
                       bbox=dict(facecolor='white',edgecolor='white'))

            
            plt.xlabel(r'$\log\ ||Ax-b||^2$', fontsize=fontsize)
            plt.ylabel(r'$\log\ ||x||^2$', fontsize=fontsize)
            
            ax.set_axisbelow(True)
            ax.grid(True)
            cbar=plt.colorbar(sc)

            l0,l1=np.amin(l),np.amax(l)
            cbar.set_clim(l0,l1)
            #cbar.solids.set_rasterized(True)
            cbar.solids.set_edgecolor("face")
            cbar.ax.set_ylabel(r"$\log\ \ell$",rotation=90,\
                               fontsize=int(1.1*fontsize))
            plt.tight_layout()
            pdf.savefig(fig)


            
            # make curvature plot
            fig,ax=plt.subplots()
            
                        
            ln=ax.plot(l,curv,'-k',linewidth=1.,zorder=1)
            
            sc=ax.scatter(l,curv,c=l,zorder=2,\
                          vmin=np.amin(l),vmax=np.amax(l),\
                          s=40,cmap=cmap,\
                          edgecolors='k',marker='o')            
            plt.xlabel(r'$\log\ \ell$', fontsize=fontsize)
            plt.ylabel(r'curvature', fontsize=fontsize)
            plt.xlim([l0,l1])
            ax.set_axisbelow(True)
            ax.grid(True)

            plt.tight_layout()
            pdf.savefig(fig)

            #plt.savefig(filename)

    @property
    def logfrob(self):
        return np.log10(self.frob)
            
    def __call__(self,root,plot=True,data=True):
        if plot: self.plot('{}_lcv.pdf'.format(root))
        if data: self.write('{}_lcv.dat'.format(root))

        
      
if __name__=='__main__':
    t=LCurve()
    t.load('test_lcv.dat')
    
    t.plot('test_lcv.png')
    
