import numpy as np
from shapely.geometry import Polygon
from scipy.spatial import ConvexHull

from pylinear import h5table
from pylinear.utilities import indices,pool,convexhull


TTYPE='DDT'

def groupFLT(flt,sources,extconf,path,minarea=0.1):
    
    
    # get the FLTs' polygons
    with h5table.H5Table(flt.dataset,TTYPE,path=path) as h5:

        for detname,detimg in flt:
            h5det=h5[detname]
            detconf=extconf[detname]
            
            for beam,beamconf in detconf:
                h5beam=h5det[beam]
                
                ids=[]
                polys=[]
                
                for segid,src in sources:
                    # read the DDT
                    ddt=h5table.DDT(src.segid)
                    ddt.readH5(h5beam)
                    if len(ddt)!=0:
                        
                        # collect the points accordingly
                        xyg=ddt.xyg.to_numpy
                        xyg=indices.unique(xyg)
                        x,y=indices.one2two(xyg,detimg.naxis)
                        #pts=np.array([x,y]).T

                        # try making the ConvexHull
                        #try:
                        with open('test.dat','w') as fp:
                            for xx,yy in zip(x,y):
                                print(xx,yy,file=fp)
                                
                        
                        xh,yh=convexhull.vertices(x,y)
                        xy=list(zip(xh,yh))
                        
                        
                        #    msg='[alarm]ConvexHull failed: {}'.format(segid)
                        #    print(len(x),pts.shape)
                        #    q=input()

                        # get the (x,y) pairs to make a polygon
                        #xy=[(pts[v,0],pts[v,1]) for v in hull.vertices]
                        poly=Polygon(xy)

                        # save the results
                        ids.append(list(segid))
                        polys.append(poly)
    # At this point, we've made shapely.Polygons out of each DDT
        

                        
    # now group those FLTs' 
    data=list(zip(ids,polys))
    nnew=ndata=len(ids)
    while nnew!=0:
        groups=[]


        while len(data)!=0:
            thisid,thispoly=data.pop(0)

            ids=thisid
            for i,(testid,testpoly) in enumerate(data):
                inter=thispoly.intersection(testpoly)
                area=inter.area
                if area>minarea:
                    thispoly=thispoly.union(testpoly)
                    data.pop(i)

                    ids.extend(testid)
            groups.append((ids,thispoly))
        data=groups
        nnew=ndata-len(data)
        ndata=len(data)

    # return the lists
    ids=set(list(zip(*groups))[0])
    #if (len(ids)==1) or isinstance(ids,np.uint32):
    #    ids=list(ids)
    return ids
        

def groupIDs(data):
    print("[info]Grouping the FLT groups")
    
    # group those IDs
    nnew=ndata=len(data)
    while nnew!=0:
        new=[]
        while len(data)!=0:
            this=data.pop(0)
            
            for i,test in enumerate(data):
                if len(this.intersection(test))!=0:
                    this=this.union(test)
                    data.pop(i)
            new.append(this)
        data=new
        n=len(data)
        nnew=ndata-n
        ndata=n
    return data


def makeGroups(conf,grisms,sources,extconf):
    print("[info]Starting the grouping algorithm")
   
    path=conf['tables']['path']
    
    # group within an FLT
    #ids=[groupFLT(flt,sources,extconf,path) for fltname,flt in grisms]

    # use the pool to group the FLTs
    p=pool.Pool(ncpu=conf['cpu']['ncpu'])
    ids=p(groupFLT,grisms.values,sources,extconf,path)
    
    # group those IDs
    data=groupIDs(ids)
    
    # make data for output
    out=[datum for datum in data]

    # print something for something's sake
    print("[info]Done grouping. Found {} groups.".format(len(out)))
    
    return out
