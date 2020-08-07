import numpy as np
from shapely import geometry

from ... import h5table
from ...utilities import pool



def group_polygons(data,minarea=0.1):
    nnew=ndata=len(data)

    while nnew!=0:
        groups=[]

        while len(data)!=0:
            thisid,thispoly=data.pop(0)
            
            for i,(testid,testpoly) in enumerate(data):
                inter=thispoly.intersection(testpoly)
                if inter.area > 0.:
                    print(inter.area,testpoly.area,thispoly.area)
                
                    r1=inter.area/testpoly.area
                    r2=inter.area/thispoly.area
                    if r1 > minarea and r2 > minarea:                
                        data.pop(i)
                        
                        thispoly=thispoly.union(testpoly)
                        thisid.extend(testid)
            groups.append((thisid,thispoly))

        N=len(data)
        data=groups
        nnew=ndata-N
        ndata=N

    return groups

def group_ids(data):
    print("[info]Grouping the IDs")
    
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
    

                    
def group_grism(grism,sources,beams,path):
    

    # open the file for a given grism
    with h5table.H5Table(grism.dataset,path=path,mode='r') as h5tab:
        groups=[]
        for device in grism:


            # first convert each source to a polygon
            polys=[]
            ids=[]
            for source in sources:

                # make a Multipolygon for each source
                poly=[]
                for beam in beams:

                    # open the files
                    h5tab.open_table(device.name,beam,'pdt')

                    # read the data
                    odt=h5tab.load_from_file(source,beam,'odt')
                    ovt=odt.compute_vertices()
                    this_poly=ovt.as_polygon()
                    
                    ## read the data 
                    #ovt=h5tab.load_from_file(source.name,'ovt',beam)
                    #
                    ## get the polygon representation
                    #this_poly=ovt.as_polygon()


                    # record it in the list
                    poly.append(this_poly)


                # make a multipolygon over beams
                poly=geometry.MultiPolygon(poly)

                # make a multipolgon
                polys.append(poly) #geometry.MultiPolygon(poly))
                ids.append([source.segid])
                
            data=list(zip(ids,polys))

            # now group these polygons for a given device
            grouped=group_polygons(data)

            # update the groups
            groups.append(grouped)


    # get a list of the segids as a list of lists
    segids=list(list(zip(*groups[0]))[0])

    #groups=list(zip(*groups))[0]
    #segids=list(zip(*groups))[0]

    #print(segids)

    
    #ids=[set(group) for group in groups]
    ids=[set(i) for i in segids]

    
    # now group these IDs for the different devices
    ids=group_ids(ids)
    
    # return the SEGIDs that collide
    return ids


def make_groups(grisms,sources,beams,path):
    print('[info]Starting the group algorithm')
    

    # use the pool to group the FLTs
    p=pool.Pool(group_grism,desc='Grouping grisms',ncpu=1)
    #ids=p(grisms.values(),sources,beams,path)
    ids=[group_grism(f,sources,beams,path) for f in grisms]
    
    # make the list of lists a list of sets
    sets=[]
    for i in ids:
        sets.extend(i)
    del ids
        
    # group those IDs
    data=group_ids(sets)
    ndata=len(data)

    # now sort them in reverse order
    if ndata!=0:
        data.sort(key=len)
        data.reverse()
    
    # print something for something's sake
    print("[info]Done grouping. Found {} groups.\n".format(ndata))
    
    return data
