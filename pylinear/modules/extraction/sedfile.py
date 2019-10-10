import h5py
import numpy as np
from collections import OrderedDict
import matplotlib.pyplot as plt


''' A simple class to read the h5 spectral file '''




class SEDFile(object):
    def __init__(self,filename):
        self.filename=filename

    def plotSpectrum(self,segid):
        sed=self.spectrum(segid,return_attrs=False,return_data=True)
        if sed is not None:

            fluxscl=self.h5.attrs['fluxscale']
            s=str(fluxscl).split('e')
            if len(s)==2:
                ex='10^{'+s[1]+'}'
                if s[0]=='1':
                    s=ex                    
                else:
                    s=s[0]+r'\times'+ex

                s='$'+s+'$ '
            else:
                s=' '
                
            
            fig = plt.figure()
            ax = plt.axes()
            ax.grid(True)
            ax.set_xlabel(r'$\lambda$ [$\mathrm{\AA}$]')
            ax.set_title('segid = {}'.format(segid))
            ax.set_ylabel(r'$f_\lambda$ ['+s+'erg s$^{-1}$ cm$^{-2}$ $\mathrm{\AA}^{-1}$]')

            
            ax.plot(sed['lam'],sed['flam'])
            ax.errorbar(sed['lam'],sed['flam'],yerr=(sed['flo']/10000.,sed['fhi']/10000.))
                        
            fig.tight_layout()
            plt.show()
    

            
    def spectrum(self,segid,**kwargs):
        return self._getData(segid,self.h5s,**kwargs)
   
    def group(self,grpid,**kwargs):
        return self._getData(grpid,self.h5g,**kwargs)

    @property
    def segIDs(self):
        s=[int(k) for k in self.h5s.keys()]
        return s

    @property
    def groupIDs(self):
        g=[int(k) for k in self.h5g.keys()]
        return g
    
        
    def _getData(self,item,h5,return_attrs=False,return_data=True):
        data=None              # default value
        attrs=OrderedDict()    # default value

        # h5 requires we work with strings
        sItem=str(item)
        if sItem in h5:
            h5d=h5[sItem]
            if return_data:      # if need to return data
                data=h5d[:]
            if return_attrs:     # if need to return attributes
                for k,v in h5d.attrs.items():
                    if isinstance(v,bytes):
                        v=v.decode('UTF-8')
                    attrs[k]=v
            

        if return_attrs:
            data=(data,attrs)
        return data

    def close(self):
        if self.h5:
            self.h5.close()

    def __enter__(self):
        self.h5=h5py.File(self.filename,'r')
        self.h5g=self.h5['GROUPS']
        self.h5s=self.h5['SPECTRA']
        self.h5c=self.h5['CONFIG']
        return self

    def __exit__(self,etype,eval,etrace):
        self.close()

    def __del__(self):
        self.close()

if __name__=='__main__':
    with SEDFile("../../../test2/test.h5") as h:
        h.plotSpectrum(2)

        
