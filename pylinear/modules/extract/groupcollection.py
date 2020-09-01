import numpy as np
from shapely import geometry
import h5py


from ... import h5table
from ...utilities import pool
from ...constants import COMPARGS,SEGTYPE



class GroupCollection(list):
    def __init__(self,minarea=0.1,ncpu=0,path='tables'):
 
        self.minarea=minarea
        self.path=path
        self.ncpu=ncpu







    def group(self,grisms,sources,beams):

        print('[info]Starting the group algorithm')

        
        p=pool.Pool(self.group_grism,desc='Grouping grisms',ncpu=self.ncpu)
        
        ids=p(grisms.values(),sources,beams)
        #ids=[group_grism(f,sources,beams,path) for f in grisms]
    
        # convert the list of lists a list of sets
        sets=[]
        for i in ids:
            sets.extend(i)
                    

    
        # group those IDs
        groups=self.group_ids(sets)
        
        #data=group_ids(sets)


        
        ## now sort them in reverse order
        if len(groups)!=0:
            groups.sort(key=len)

            # put them in in reverse order
            for group in reversed(groups):
                self.append(group)


        
        # print something for something's sake
        print("[info]Done grouping, found {} groups.\n".format(len(self)))


    def append(self,data):
        super().append(tuple(data))

        
    def write_h5(self,grpfile):
        with h5py.File(grpfile,'w') as h5:
            h5.attrs['ngroup']=np.uint32(len(self))
            for grpid,segids in enumerate(self):
                name=str(grpid)
                hd=h5.create_dataset(name,data=np.array(segids,dtype=SEGTYPE),
                                     **COMPARGS)
                
                hd.attrs['nobj']=np.uint32(len(segids))
                

    @classmethod
    def load_h5(cls,grpfile,**kwargs):
        obj=cls(**kwargs)
        with h5py.File(grpfile,'r') as h5:
            for v in h5.values():
                obj.append(list(v[:]))
        return obj
        
    def write_ascii(self,grpfile):
        with open(grpfile,'w') as fp:
            for grpid,grp in enumerate(self):
                for segid in grp:
                    print(grpid,segid,file=fp)
                    

    @classmethod
    def load_ascii(cls,grpfile,**kwargs):
        obj=cls(**kwargs)

        grpids,segids=np.loadtxt(grpfile,unpack=True,dtype=(np.uint,SEGTYPE))

        grpids,grpnums=np.unique(grpids,return_counts=True)
        
        # this is basically what np.split does, but i want it liek this
        # since i will caste it as a list anyway
        i=0
        for num in grpnums:
            j=i+num
            obj.append(segids[i:j])
            i=j
            
       
        return obj



        
    def group_polygons(self,data):
        nnew=ndata=len(data)

        while nnew!=0:
            groups=[]

            while len(data)!=0:
                thisid,thispoly=data.pop(0)
            
                for i,(testid,testpoly) in enumerate(data):
                    inter=thispoly.intersection(testpoly)

                    if (inter.area > self.minarea*testpoly.area) and \
                       (inter.area > self.minarea*thispoly.area):
                        data.pop(i)
                        thispoly=thispoly.union(testpoly)
                        thisid.extend(testid)

                groups.append((thisid,thispoly))

            N=len(data)
            data=groups
            nnew=ndata-N
            ndata=N

        return groups

    def group_ids(self,data):
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

    def group_grism(self,grism,sources,beams):
        
        # open the file for a given grism
        with h5table.H5Table(grism.dataset,path=self.path,mode='r') as h5tab:
            groups=[]
            for device in grism:

                # first convert each source to a polygon
                polys=[]
                ids=[]
                for i,source in enumerate(sources):
                    
                    # make a Multipolygon for each source
                    poly=[]
                    for beam in beams:

                        # open the files
                        if i ==0:
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
                grouped=self.group_polygons(data)

                # update the groups
                groups.append(grouped)


        # get a list of the segids as a list of lists
        segids=list(list(zip(*groups[0]))[0])

        #groups=list(zip(*groups))[0]
        #segids=list(zip(*groups))[0]

        
        #ids=[set(group) for group in groups]

        # convert the list of lists into a list of sets
        ids=[set(i) for i in segids]
        
    
        # now group these IDs for the different devices
        ids=self.group_ids(ids)
    
        # return the SEGIDs that collide
        return ids

    
