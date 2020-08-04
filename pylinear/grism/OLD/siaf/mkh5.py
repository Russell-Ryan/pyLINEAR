import h5py
from astropy.io import fits
import numpy as np
import re
import pysiaf


def write_sip(h5,hdr):
    
    dtype=np.dtype([('i',np.uint8),('j',np.uint8),('val',float)])

    
    for let in ['A','B','AP','BP']:
        order='{}_ORDER'.format(let)
                
        if order in hdr:
            i,j,v=[],[],[]
            regex=re.compile('{}_[0-9]+_[0-9]+'.format(let))
                    
            for key,val in hdr.items():
                if regex.match(key):
                    spl=key.split('_')
                    i.append(np.uint8(spl[1]))
                    j.append(np.uint8(spl[2]))
                    v.append(val)

                    
            data=np.array(list(zip(i,j,v)),dtype=dtype)
            hd=h5.create_dataset(let,data=data,dtype=dtype)
            hd.attrs['order']=hdr[order]
    return h5
        
def write_meta(h5,dic):


    h5.attrs['CHIP']=np.uint8(dic['chip'])
    h5.attrs['V2']=np.float32(dic['v2'])
    h5.attrs['V3']=np.float32(dic['v3'])
    h5.attrs['V3X']=np.float32(dic['v3x'])
    h5.attrs['V3Y']=np.float32(dic['v3y'])
    h5.attrs['XSCL']=np.float64(dic['xscl'])
    h5.attrs['YSCL']=np.float64(dic['yscl'])
    h5.attrs['XREF']=np.float32(dic['xref'])
    h5.attrs['YREF']=np.float32(dic['yref'])
    h5.attrs['NAXIS1']=np.uint32(dic['naxis1'])
    h5.attrs['NAXIS2']=np.uint32(dic['naxis2'])
    h5.attrs['CRPIX1']=np.float32(dic['crpix1'])
    h5.attrs['CRPIX2']=np.float32(dic['crpix2'])

    return h5    



def jwst(h5):
    hf=h5.require_group('JWST')
    return hf




def hst(h5):
    hf=h5.require_group('HST')
    return hf


def wfc3uvis(h5):
    h=hst(h5)


    hf=h.require_group('WFC3UVIS1')
    dic={'chip':1,'v2':30.6556,'v3':25.2168,'v3x':-41.2625,'v3y':44.8312,
         'xscl':0.039637,'yscl':0.039365,'xref':2073,'yref':1026,
         'naxis1':4096,'naxis2':2051,'crpix1':2048,'crpix2':1026}
    h5=write_meta(hf,dic)

    filename='/Users/rryan/LINEAR/config/HST/WFC3/UVIS/hst_wfc3_uvis_fov.fits'
    hdr=fits.getheader(filename,ext=2)
    hf=write_sip(hf,hdr)




    hf=h.require_group('WFC3UVIS2')
    
    dic={'chip':2,'v2':-27.4596,'v3':-33.2604,'v3x':-41.6335,'v3y':44.7671,
         'xscl':0.039858,'yscl':0.039837,'xref':2073,'yref':1026,
         'naxis1':4096,'naxis2':2051,'crpix1':2048,'crpix2':1026}
    h5=write_meta(hf,dic)

    filename='/Users/rryan/SIRAH/supernovae/sn2020bpi/epoch1/data/ie5420g3q_flt.fits'
    hdr=fits.getheader(filename,ext=1)
    hf=write_sip(hf,hdr)
    
    

def wfc3ir(h5):
    h=hst(h5)

    
    hf=h.require_group('WFC3IR')

    
    dic={'chip':1,'v2':0.6309,'v3':8.6778,'v3x':-45.1232,'v3y':44.5888,
         'xscl':0.135601,'yscl':0.121307,'xref':562,'yref':562,
         'naxis1':1014,'naxis2':1014,'crpix1':507,'crpix2':507}
    h5=write_meta(hf,dic)

    filename='/Users/rryan/SIRAH/supernovae/sn2020bpi/epoch1/data/ie5420g3q_flt.fits'
    hdr=fits.getheader(filename,ext=1)
    hf=write_sip(hf,hdr)

    return hf

if __name__=='__main__':
    with h5py.File('siaf.h5','w') as h5:
        wfc3ir(h5)
        wfc3uvis(h5)
        

        
