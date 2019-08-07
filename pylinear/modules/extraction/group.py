import numpy as np
from shapely.geometry import Polygon
from scipy.spatial import ConvexHull

from pylinear import h5table
from pylinear.utilities import progressbar,indices


TTYPE='DDT'

def groupFLT(flt,sources,extconf,path):
    print("[info]Grouping the FLTs")
    minarea=0.1
    
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
                    ddt=h5table.DDT(src.segid)
                    ddt.readH5(h5beam)
                    if len(ddt)!=0:
                        
                        xyg=ddt.xyg.to_numpy
                        xyg=indices.unique(xyg)
                        x,y=indices.one2two(xyg,detimg.naxis)
                        pts=np.array([x,y]).T
                        
                        hull=ConvexHull(pts)
                        
                        xy=[(pts[v,0],pts[v,1]) for v in hull.vertices]
                        ids.append(segid)
                        polys.append(Polygon(xy))
                        

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


def makeGroups(conf,grisms,sources,extconf,dtype=None):
    print("[info]Starting the grouping algorithm")
    if dtype is None: dtype=np.uint16

    path=conf['tables']['path']

    # group within an FLT
    ids=[groupFLT(flt,sources,extconf,path) for fltname,flt in grisms]

    # group those IDs
    data=groupIDs(ids)
    
    # make data for output
    out=[datum for datum in data]

    # print something for something's sake
    print("[info]Found {} groups.".format(len(out)))
    
    return out
