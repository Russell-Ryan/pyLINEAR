import numpy as np
from specutils import Spectrum1D
from astropy import units as u
import matplotlib.pyplot as plt
from astropy.nddata import StdDevUncertainty



wave,tran = np.loadtxt('hst_wfc3_f105w.filt',usecols=(0,1),unpack=True)


lamb=np.arange(7500,15001,25,dtype=np.float)

flam=np.sin((lamb-7500)/7500*2*np.pi)+2.
func=np.full_like(lamb,0.2)

unit=u.Unit('1e-17 erg s-1 cm-2 angstrom-1')
#flam*=u.Unit('1e-17 erg s-1 cm-2 angstrom-1')
#func*=u.Unit('1e-17 erg s-1 cm-2 angstrom-1')
#lamb*=u.AA
func=StdDevUncertainty(func)

sed=Spectrum1D(flux=flam,spectral_axis=lamb,uncertainty=func,unit=unit,spectral_axis_unit=u.AA)


ax = plt.subplots()[1]
ax.plot(sed.spectral_axis, sed.flux)
ax.set_xlabel("Dispersion")
ax.set_ylabel("Flux")
plt.show()



