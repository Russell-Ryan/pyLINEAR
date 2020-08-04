''' Functions to perform some image operations on an image with segmap. '''



def smooth(seg,img,segid,filtsig,key='FILTSIG'):
    ''' smooth with Gaussian filter '''

    
    if filtsig is None or filtsig <=0:
        return seg,img
        
    bad=seg.data != segid
    good=seg.data == segid
    V=img.data.copy()
    V[bad]=0
    VV=sn.gaussian_filter(V,sigma=filtsig)

    W=np.ones_like(img.data)
    W[bad]=0
    WW=sn.gaussian_filter(W,sigma=filtsig)
    Z=VV/WW
    img.data[good]=Z[good]
    
    seg[key]=filtsig
    
    return seg,img
        
def erode(seg,img,segid,eroderad,key='ERODERAD'):
    ''' Erode the segmentation map '''

    
    if eroderad is None or eroderad<=0:
        return seg,img
    
    dim=np.int(2*eroderad+1)
    kern=np.ones((dim,dim),dtype=np.int)
    
    good=seg == segid
    
    flux0=np.sum(img[np.where(good)])
    
    eroded=sn.binary_erosion(good,structure=kern).astype(np.int)
    
    b=np.where((seg != 0) & (seg != segid))
    g=np.where(eroded)
    eroded[g]=seg[g]
    eroded[b]=seg[b]
    
    flux1=np.sum(img[g])
        

    if flux0<=0 or flux1<=0:
        print("[warn]Fluxes are <=0: {} {}".format(flux0,flux1))
        print('[warn]scale the weights by this amount? or apply it post facto?')
        frat=1.
    else:
        frat=flux0/flux1
        
        
    seg.image=eroded
    seg[key]=eroderad

    return seg,img

def isophotal(seg,img,segid,sblim,key='SBLIM'):
    ''' Trim the segmap to a fixed surface brightness '''
    
    if sblim is None:
        return seg,img    
    print('[debug]will need the zweropoint (now in the self)')
        
def maxsize(seg,img,segid,maxrad,key='MAXRAD'):
    ''' Trim the segmap by a maximum size '''
    if maxrad is None or maxrad <= 0:
        return seg,img    
    print('[debug]Not ready')

    
def rebin(seg,img,segid,binfact,function='mean',key='BINFACT'):
    ''' Rebin the image and segmap by some factor '''

    #print('appears to use numpy.reshape and mean.  not sure yet')
    # in IDL, i used any pixel that contains info

        
    if binfact is None or binfact <=1:
        return seg,img
        

    binfact=int(binfact)
        
        
    print("[debug]this is all to change with  FITSImage")
    q=input()

        
    dim=img.shape
    new=[(dim[0]+1)//binfact,(dim[1]+1)//binfact]
    bins=np.arange(dim[0]*dim[1]).reshape(dim)+1
    ones=np.ones((binfact,binfact),dtype=np.int)
    bins=np.kron(bins,ones)[:dim[0],:dim[1]]
    b=np.unique(bins)
    
    flo=function.lower()
    if flo=='mean': func=sn.mean
    elif flo=='sum': func=sn.sum
    elif flo=='median': func=sn.median
    else: func=sn.mean
    ave=func(img.data,labels=bins,index=b).reshape(new)
    
    img.data=ave
    img.naxis[0]=img.header['NAXIS1']=new[0]
    img.naxis[1]=img.header['NAXIS2']=new[1]
    img.crpix[0]=img.header['CRPIX1']=(img.header['CRPIX1']+0.5)/binfact+0.5
    img.crpix[1]=img.header['CRPIX2']=(img.header['CRPIX2']+0.5)/binfact+0.5
    img.cd[0,0]=img.header['CD1_1']=img.header['CD1_1']*binfact
    img.cd[1,0]=img.header['CD2_1']=img.header['CD2_1']*binfact
    img.cd[0,1]=img.header['CD1_2']=img.header['CD1_2']*binfact
    img.cd[1,1]=img.header['CD2_2']=img.header['CD2_2']*binfact
    
    g=np.where((seg.data != segid))[0]
    mx=seg.data
    mx[g]=0
    mx=sn.maximum(mx,labels=bins,index=b).reshape(new)
    zz=sn.maximum(seg.data,labels=bins,index=b).reshape(new)
    g=np.where(mx==0)[0]
    mx[g]=zz[g]
    
    seg.data=mx
    seg.naxis[0]=seg.header['NAXIS1']=new[0]
    seg.naxis[1]=seg.header['NAXIS2']=new[1]
    seg.crpix[0]=seg.header['CRPIX1']=(seg.header['CRPIX1']+0.5)/binfact+0.5
    seg.crpix[1]=seg.header['CRPIX2']=(seg.header['CRPIX2']+0.5)/binfact+0.5
    seg.cd[0,0]=seg.header['CD1_1']=seg.header['CD1_1']*binfact
    seg.cd[1,0]=seg.header['CD2_1']=seg.header['CD2_1']*binfact
    seg.cd[0,1]=seg.header['CD1_2']=seg.header['CD1_2']*binfact
    seg.cd[1,1]=seg.header['CD2_2']=seg.header['CD2_2']*binfact
    
    
    return seg,img

