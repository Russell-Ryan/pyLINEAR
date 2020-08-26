from astropy.table import Table
import numpy as np


def read_ascii_table(filename,**kwargs):
    tab=Table.read(filename,format='ascii.no_header',**kwargs)

    meta={}
    if tab.meta:
        if 'comments' in tab.meta:
            for m in tab.meta['comments']:
                m=m.split('=')
                if len(m)==2:
                    k,v=m[0].strip(),m[1].strip()
                    try:
                        v=int(v)
                    except:
                        try:
                            v=float(v)
                        except:
                            if v=='':
                                v=None
                                
                    meta[k]=v
    return tab,meta

def read_ascii_columns(filename,**kwargs):
    tab,meta=read_ascii_table(filename,**kwargs)
    cols=[np.array(c) for c in tab.itercols()]
    return cols,meta

if __name__=='__main__':
    #(lamb,tran),meta = read_ascii_columns('hst_acs_f814w.filt',names=('lamb','tran'))
    #print(lamb)


    filename='/Users/rryan/pylinear/training/notebooks/t.dat'
    (a,b,c,d,e),meta=read_ascii_columns(filename)

    print(meta)
