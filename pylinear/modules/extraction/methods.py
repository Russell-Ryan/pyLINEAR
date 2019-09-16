import numpy as np
import inspect

def printDamping(value,frob,optimal=True):
    ''' Simple utility to print a message. '''

    opt='optimized' if optimal else ''
    
    # https://www.utf8-chartable.de/unicode-utf8-table.pl?number=1024&utf8=dec
    print('')
    print("[info]pyLINEAR results: {}".format(opt))
    print("  unscaled log(\u2113) = {}".format(value))
    print("    scaled log(\u2113) = {}".format(value+np.log10(frob)))
    #print("          \u221a||A||\u00b2 = {}".format(frob))
    #print("   \u01c1   \u01c1 = {}".format(frob))
    #print(" \u221a\u01c1\u03a3a\u00b2\u01c1 = {}".format(frob))
    print("              \u01c1A\u01c1 = {}".format(frob))
    print("           method = {}".format(inspect.stack()[1][3]))
    print('')
    
def menger(xyj,xyk,xyl):
    ''' Compute the curvature from three (x,y) pairs. '''
    
    a=xyj[0]*xyk[1]+xyk[0]*xyl[1]+xyl[0]*xyj[1]
    b=xyj[0]*xyl[1]+xyk[0]*xyj[1]+xyl[0]*xyk[1]
    num=2*(a-b)

    
    djk=(xyk[0]-xyj[0])**2+(xyk[1]-xyj[1])**2
    dkl=(xyl[0]-xyk[0])**2+(xyl[1]-xyk[1])**2
    dlj=(xyj[0]-xyl[0])**2+(xyj[1]-xyl[1])**2
    den=np.sqrt(djk*dkl*dlj)
    curv=num/den
    return curv





def gridSearch(logdamp,mat,x0):
    ''' Iterate through log(damp) values and find point of max curvature. '''
    
    print('[info]Starting grid search')
    # determine some log damping values
    ldamp=np.arange(logdamp[0],logdamp[1]+logdamp[2],logdamp[2])
    
    # run LSQR for all those
    results=mat.runLSQR(ldamp,x0=x0)

    # find the maximum curvature
    n=len(results)
    curv=np.full(n,np.nan)
    for i in range(1,n-1,1):
        j,k=i-1,i+1
        curv[i]=menger(results[j].xy,results[i].xy,results[k].xy)
        
    # select the result with maximum curvature        
    i=np.nanargmax(curv)
    out=results[i]
    
    # show a message and return
    printDamping(out.logdamp,mat.frob)
    return out

def goldenSearch(logdamp,mat,x0):
    ''' Find point of maximum curvature following Cultrera Golden Search. '''

    print('[info]Starting golden search')
    # set some constants
    phi=(1.+np.sqrt(5.))/2.
    eps=logdamp[2]
    
    # initialize the logdamp values: x = log(damp)
    x1,x4=logdamp[0],logdamp[1]
    x2=(x4+phi*x1)/(1+phi)
    x3=x1+(x4-x2)

    # set the current state
    state=mat.runLSQR([x1,x2,x3,x4],x0=x0)
    state=[None,*state]

    # start the Cultrera algorithm
    while (state[4].damp-state[1].damp) > eps*state[4].damp:
        c2=menger(state[1].xy,state[2].xy,state[3].xy)
        c3=menger(state[2].xy,state[3].xy,state[4].xy)
        
        while c3<0:
            state[4]=state[3]
            state[3]=state[2]

            x2=(state[4].logdamp+phi*state[1].logdamp)/(1+phi)
            state[2]=mat.runLSQR(x2,x0=x0)

            c3=menger(state[2].xy,state[3].xy,state[4].xy)
            
        if c2>c3:
            state[0]=state[2]     # optimal solution
            state[4]=state[3]
            state[3]=state[2]
            
            x2=(state[4].logdamp+phi*state[1].logdamp)/(1+phi)
            state[2]=mat.runLSQR(x2,x0=x0)
            
        else:
            state[0]=state[3]     # optimal solution
            state[1]=state[2]
            state[2]=state[3]

            x3=state[1].logdamp+(state[4].logdamp-state[2].logdamp)
            state[3]=mat.runLSQR(x3,x0=x0)

                        
    # the output
    out=state[0]

    # print a message and return the state
    printDamping(out.logdamp,mat.frob)
    return out

def fixedDamping(logdamp,mat,x0):
    ''' Just run do a single value of log(damp). '''

    print('[info]Starting fixed damping')
    
    # Run LSQR
    if isinstance(logdamp,list):
        raise ValueError("Fixed extraction can have only a scalar damping.")
    result=mat.runLSQR(logdamp,x0=x0)

    # show result and return
    printDamping(result.logdamp,mat.frob,optimal=False)
    return result
    
