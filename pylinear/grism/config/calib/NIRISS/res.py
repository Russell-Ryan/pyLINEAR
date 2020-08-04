import glob
from pylinear2.grism.config import beam
import os
import numpy as np

os.environ['PYLINEAR_CONFIG']+='/NIRISS'


files=glob.glob('*conf')

DLAMB=47.

for f in files:
    first=f[:18]
    if first=='NIRISS_F150W_GR150':
        LAMB0=12800



    b=beam.Beam(f,'A')
    lamb0=b.sensitivity.wmin*1e4
    lamb1=b.sensitivity.wmax*1e4
    dlamb=b.dispersion((1024,1024))*1e4

    dl=np.ceil(dlamb)
    
    nlamb=int(np.ceil((lamb1-lamb0)/DLAMB))
    

    
    print(f)
    print(lamb0,lamb1,dlamb,nlamb)
    #print(dl)
