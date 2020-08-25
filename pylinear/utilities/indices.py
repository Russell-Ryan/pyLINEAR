import numpy as np

ONE=np.uint(1)

def compress(indices):
    unique_indices=np.unique(indices)
    compressed_indices=np.digitize(indices,unique_indices)-1
    return compressed_indices,unique_indices

def unique(indices):
    #indexes = np.unique(indices, return_index=True)[1]
    #unique_indices=[indices[index] for index in sorted(indexes)]
    #for ii,jj in zip(indices,unique_indices):
    #    print(ii,jj)
    idx = np.unique(indices, return_index=True)[1]
    unique_indices=indices[np.sort(idx)]
    return unique_indices

def decimate(indices,values):
    compressed_indices,unique_indices=compress(indices)
    decimated_values=np.bincount(compressed_indices,weights=values)
    return decimated_values,unique_indices

def average(indices,values):
    compressed_indices,unique_indices=compress(indices)
    decimated_values=np.bincount(compressed_indices,weights=values)
    decimated_counts=np.bincount(compressed_indices)
    decimated_values=decimated_values/decimated_counts    
    return decimated_values,unique_indices


def reverse(integers):
    uniq,ind,nums=np.unique(integers,return_inverse=True,return_counts=True)
    reverse=np.split(np.argsort(ind),np.cumsum(nums[:-1]))
    ri=list(zip(uniq,reverse))
    return ri

def one2two(xy,dim):
    y,x=np.divmod(np.array(xy),dim[0])
    return x,y

def two2one(x,y,dim):
    return np.array(x)+dim[0]*np.array(y)

def unique_pairs(x,y):

    mx=np.amax(x)+1
    shape=(mx.astype(x.dtype),)

    xy=two2one(x,y,shape)

    xx,yy=one2two(xy,shape) 
    
    xyq=unique(xy)


    xq,yq=one2two(xyq,shape)
    

    return xq,yq


if __name__=='__main__':

    x=np.array([1,2,3,4,5,3,1],dtype=np.uint64)
    y=np.array([2,3,4,5,3,4,2],dtype=np.uint64)

    
    xq,yq=unique_pairs(x,y)
    
