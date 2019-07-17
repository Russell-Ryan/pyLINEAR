# can access a column by name:
#   tab['x'] --- returns a list
# can access a row by index (probably slower):
#   tab[1] --- return a struct
# previous implies that:
#   tab[1]['x'] == tab['x'][1], but the second may be faster for big tables
# can append data to table
#   tab.append(aList)
# can read data from disk
#   tab.load(filename)
# can write data to disk
#   tab.write(filename)

class Column(object):
    def __init__(self,name):
        self._name=name
        self._width=max(len(name),8)
        self._data=[]
    def append(self,val):
        self._width=max(self.width,len(str(val)))
        self._data.append(val)
    def __len__(self):
        return len(self._data)
    def __getitem__(self,i):
        out='{0:>{width}}'.format(self._data[i],width=self._width)
        return out
    

    def __setitem__(self,i,v):
        self._data[i]=v

    def value(self,i):
        return self._data[i]

        
    @property
    def data(self):
        return self._data

    @data.setter
    def data(self,d):
        if len(d)==len(self._data):
            self._data=d
            
    @property
    def name(self):
        return '{:>{width}}'.format(self._name,width=self._width)
    
    @name.setter
    def name(self,name):
        self.name=str(name)

    @property
    def width(self):
        return self._width
    @width.setter
    def width(self,w):
        if isinstance(w,int):
            self._width=w
        else:
            print("width must be an integer")
        
    @property
    def line(self):
        return self._width*'-'
    
class AsciiTable(object):
    def __init__(self,names,filename=None,**kwargs):
        self.names=names
        self.columns=[]
        self.count=0
        for name in names:
            self.columns.append(Column(name))
        if filename is not None:
            self.load(filename,**kwargs)

    def append(self,data):
        for d,c in zip(data,self.columns):
            c.append(d)
        self.count+=1

    def __iter__(self):
        if len(self.columns)==1:
            for c in self.columns[0].data:
                yield c
        else:
            data=[c.data for c in self.columns]
            for args in zip(*data):
                yield args
        
        
        
    def __getitem__(self,key):
        if isinstance(key,str):
            index=self.names.index(key)
            out=self.columns[index].data
        elif isinstance(key,int):
            out={}
            for c in self.columns:
                out[c.name.strip()]=c.value(key)
        elif isinstance(key,tuple):
            out=[]
            for k in key:
                out.append(self[k])
            out=tuple(out)
        elif isinstance(key,slice):
            start=key.start or 0
            stop=key.stop or self.count
            step=key.step or 1
            out=[]
            for i in range(start,stop,step):
                out.append(self[i])
            if len(out) ==1:
                out=out[0]
        else:
            raise NotImplementedError("Invalid key instance.")
        return out

    def __setitem__(self,key,value):
        if isinstance(key,str):
            index=self.names.index(key)
            self.columns[index].data=value
        elif isinstance(key,int):
            if len(value)==len(self.columns):
                for v,c in zip(value,self.columns):
                    c[key]=v
        elif isinstance(key,slice):
            print('set slice')
        else:
            raise NotImplementedError("Invalid key instance.")

    
    def __str__(self):
        header=[c.name for c in self.columns]
        out='|'.join(header)+'\n'
        line=[c.line for c in self.columns]
        out=out+'+'.join(line)+'\n'
        for i in range(self.count):
            line=[c[i] for c in self.columns]
            out=out+'|'.join(line)
            if i < self.count-1:
                out=out+'\n'
            
        return out

    def __len__(self):
        return self.count
        

    
    def remove(self,key):
        raise NotImplementedError("if key is int, remove row.  if key is str, remove column")

    def merge(self,tab):
        raise NotImplementedError('merge two tables')
    
    def write(self,filename,delim=' '):
        with open(filename,'w') as fp:
            for i,c in enumerate(self.columns):
                line='# {}: {}\n'.format(i+1,c.name)
                fp.write(line)
            for i in range(self.count):
                line=[c[i] for c in self.columns]
                out=delim.join(line)+'\n'
                fp.write(out)

    def load(self,filename,comments=['%',';','#'],delimiter=' '):
        with open(filename,'r') as fp:
            for line in fp:
                line=line.strip()
                if line !='' and line[0] not in comments:
                    tokens=line.split(delimiter)
                    data=[]
                    for token in tokens:
                        if token != '':
                            try:
                                t=int(token)
                            except ValueError:
                                try:
                                    t=float(token)
                                except:
                                    t=token
                            data.append(t)
                    if len(data)==len(self.columns):
                        self.append(data)


    
if __name__=='__main__':
    n=100
    t=AsciiTable(['x','y','z'])
    for i in range(n):
        t.append((i,2*i,True))


    for args in t:
        print(args)


        
    t.write('test2.dat')
