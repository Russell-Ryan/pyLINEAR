import numpy as np


''' simple function to compute the menger curvature.

https://en.wikipedia.org/wiki/Menger_curvature

'''

def menger(xyj,xyk,xyl):
    ''' Compute the curvature from three (x,y) pairs. '''

    #xyj=np.array(xyj)
    #xyk=np.array(xyk)
    #xyl=np.array(xyl)


    
    
    if not np.allclose(xyj,xyk) or not np.allclose(xyk,xyl):
        
        num=2.*np.abs(xyj[0]*(xyk[1]-xyl[1])+
                      xyk[0]*(xyl[1]-xyj[1])+
                      xyl[0]*(xyj[1]-xyk[1]))
        
        djk=np.hypot(xyk[0]-xyj[0],xyk[1]-xyj[1])
        dkl=np.hypot(xyl[0]-xyk[0],xyl[1]-xyk[1])
        dlj=np.hypot(xyj[0]-xyl[0],xyj[1]-xyl[1])
        den=djk*dkl*dlj
        
        
        curv=num/den
        
    else:
        curv=0.
    
    '''
    #np.allclose(xyj,xyk),np.allclose(xyk,xyl))

    
    #xyj-=xyk
    #xyl-=xyk
    #xyk-=xyk
    #print(xyj,xyl)
    #a=xyj[0]*xyk[1]+xyk[0]*xyl[1]+xyl[0]*xyj[1]
    #b=xyj[0]*xyl[1]+xyk[0]*xyj[1]+xyl[0]*xyk[1]
    #num1=2.*np.abs(a-b)
    num=2.*np.abs(xyj[0]*(xyk[1]-xyl[1])+
                  xyk[0]*(xyl[1]-xyj[1])+
                  xyl[0]*(xyj[1]-xyk[1]))

    djk=np.hypot(xyk[0]-xyj[0],xyk[1]-xyj[1])
    dkl=np.hypot(xyl[0]-xyk[0],xyl[1]-xyk[1])
    dlj=np.hypot(xyj[0]-xyl[0],xyj[1]-xyl[1])
    den=djk*dkl*dlj


    #print(djk,dkl,dlj,den1)
    
    
    #djk=(xyk[0]-xyj[0])**2+(xyk[1]-xyj[1])**2
    #dkl=(xyl[0]-xyk[0])**2+(xyl[1]-xyk[1])**2
    #dlj=(xyj[0]-xyl[0])**2+(xyj[1]-xyl[1])**2
    #den=np.sqrt(djk*dkl*dlj)
    #print(djk,dkl,dlj,den)
    #print(den1-den)


    #print(a,b,num,den)

    if den ==0.:
        curv=0.0
    else:
        curv=num/den
    '''
    
    
    return curv


    

def vector(x,y):
    print('[alarm]this has issues with repeated values')
    
    k=np.arange(1,len(x)-1)
    j,l=k-1,k+1

    num=2.*np.abs(x[j]*(y[k]-y[l])+x[k]*(y[l]-y[j])+x[l]*(y[j]-y[k]))

    djk=(x[k]-x[j])**2+(y[k]-y[j])**2
    dkl=(x[l]-x[k])**2+(y[l]-y[k])**2
    dlj=(x[j]-x[l])**2+(y[j]-y[l])**2

    c=np.full_like(x,np.nan,dtype=np.float)
    
    c[k]=num/np.sqrt(djk*dkl*dlj)
    return c
    
