import numpy as np
from shapely.geometry import Polygon
from scipy.spatial import ConvexHull
import matplotlib.pyplot as plt

from pylinear import h5table
from pylinear.utilities import indices,pool,convexhull


TTYPE='DDT'

def groupFLT(flt,sources,extconf,path,minarea=0.1):
        
    # get the polygons for this FLT:
    with h5table.H5Table(flt.dataset,TTYPE,path=path) as h5:
        for detname,detimg in flt:
            h5det=h5[detname]
            detconf=extconf[detname]
            
            for beam,beamconf in detconf:
                h5beam=h5det[beam]
                
                ids=[]
                polys=[]

                
                #for segid,src in sources:
                for segid,src in sources.items():
                    # read the DDT
                    ddt=h5table.DDT(src.segid)
                    ddt.readH5(h5beam)
                    if len(ddt)!=0:
                        
                        # collect the points accordingly
                        xyg=ddt.xyg.to_numpy
                        xyg=indices.unique(xyg)
                        x,y=indices.one2two(xyg,detimg.shape)
                        del xyg

                        # get the vertices
                        xy=convexhull.vertices(x,y)

                        # reform to (x,y) pairs
                        xy=list(zip(*xy))

                        # make into a polygon from Shapely
                        poly=Polygon(xy)

                        # save the results
                        ids.append([segid])
                        polys.append(poly)


    # At this point, we've made shapely.Polygons out of a given DDT
    # so now we will gropu the polygons using polygon intersection
    # methods in shapely.
    
    #print('grouping the polygons for {}'.format(flt.dataset))
                        
    # group those sources with Shapely math
    data=list(zip(ids,polys))
    nnew=ndata=len(ids)
    if nnew==0:
        #print('[warn]No objects to group for {}'.format(flt.dataset))
        return []
        
    while nnew!=0:
        groups=[]


        while len(data)!=0:
            thisid,thispoly=data.pop(0)

            #ids=thisid
            for i,(testid,testpoly) in enumerate(data):
                inter=thispoly.intersection(testpoly)
                #inter=inter.area   # intersection area

                r1=inter.area/testpoly.area
                r2=inter.area/thispoly.area
                if r1 > minarea and r2 > minarea:                
                #if area>minarea:
                    data.pop(i)   # it was grouped, so remove it from the list

                    
                    #print(r1,r2)
                    #print(inter.area,testpoly.area,thispoly.area)
                    #fig,ax=plt.subplots(1,1)
                    #ax.plot(*thispoly.exterior.xy, color='#6699cc', alpha=0.7,
                    #        linewidth=3, solid_capstyle='round', zorder=2)
                    #ax.plot(*testpoly.exterior.xy, color='#cccccc', alpha=0.7,
                    #        linewidth=3, solid_capstyle='round', zorder=2)
                    #ax.set_title('Polygon')
                    #plt.show()
                    
                    # update the this
                    thispoly=thispoly.union(testpoly)
                    thisid.extend(testid)
                    
            groups.append((thisid,thispoly))
        data=groups
        nnew=ndata-len(data)
        ndata=len(data)


    # get just the IDs
    groups=list(zip(*groups))[0]

    # return a list of sets
    ids=[set(group) for group in groups]
    
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
                if this.intersection(test):
                    this=this.union(test)
                    data.pop(i)
            new.append(this)
        data=new
        n=len(data)
        nnew=ndata-n
        ndata=n
    return data


def makeGroups(conf,grisms,sources,extconf,sort=True):
    print("[info]Starting the grouping algorithm")
   
    path=conf['tables']['path']
    
    # use the pool to group the FLTs
    #p=pool.Pool(ncpu=conf['cpu']['ncpu'])
    #ids=p(groupFLT,grisms.values(),sources,extconf,path,\
    #      prefix='Grouping FLTs')
    p=pool.Pool(groupFLT,ncpu=conf['cpu']['ncpu'],desc='Grouping FLTs')
    ids=p(grisms.values(),sources,extconf,path)

    
    # convert list of lists of sets to list of sets
    sets=[]
    for i in ids:
        sets.extend(i)
    del ids
        
    # group those IDs
    data=groupIDs(sets)

    # sort them by reverse order
    if sort:
        n=[len(d) for d in data]
        data=[d for _,d in reversed(sorted(zip(n,data)))]

    
    # make data for output
    out=[datum for datum in data]
    
    # print something for something's sake
    print("[info]Done grouping. Found {} groups.\n".format(len(out)))
    
    return out
