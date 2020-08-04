import pysiaf
import numpy as np
import matplotlib.pyplot as plt

siaf=pysiaf.Siaf('nircam')
s=siaf['NRCA1_FULL']

siaf=pysiaf.Siaf('HST')

s=siaf['IIRGRSM102']
for k,v in s.__dict__.items():
    print(k,v)



crval1=84.711867666512
crval2=-69.11299787833

CRVAL1=84.696125638033
CRVAL2=-69.090802222537

XSCL=0.039365
YSCL=0.039637



pa=-165.7770460604548
orientat=-165.7770460604548

XSCL=0.135601
YSCL=0.121307
pa=131.924
cs=np.cos(pa*np.pi/180)
sn=np.sin(pa*np.pi/180)

R=np.array([[cs,-sn],[sn,cs]])
P=np.array([[-YSCL,0],[0,XSCL]])/3600.
C=R.dot(P)



#cd=np.array([[1.0876212542302E-05,2.7224465443633E-06],[2.0392199055964E-06,-1.0723507375072E-05]])

cd=np.array([[2.35007487532090E-05,-2.6169687278019E-05],[-2.9378019274077E-05,-2.1078301735985E-05]])

Rinv=np.linalg.inv(R)
print(Rinv.dot(cd)*3600.)
#print(P)
print(C)
#print(cd)


ref2=30.6556
ref3=25.2168
v3y=44.8312

obs2=-27.4596
obs3=-33.2604


print(-pa-v3y)

orientats=np.arange(0,359,0.1)
diff=np.zeros_like(orientats,dtype=np.float)
for i,orientat in enumerate(orientats):


    A = pysiaf.rotations.attitude(ref2,ref3, crval1, crval2, orientat)
                              

    # compute the new positions
    crvals = pysiaf.utils.rotations.pointing(A, obs2,obs3)
    diff[i]=(crvals[0]-CRVAL1)**2+(crvals[1]-CRVAL2)**2
    
i=np.argmin(diff)
print(orientats[i],diff[i])




A = pysiaf.rotations.attitude(ref2,ref3, crval1, crval2, -pa-v3y)
                              

# compute the new positions
crvals = pysiaf.utils.rotations.pointing(A, obs2,obs3)
print(crvals,(CRVAL1,CRVAL2))


plt.plot(orientats+(pa+v3y),diff)

#plt.show()
