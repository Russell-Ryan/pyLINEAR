from collections import OrderedDict

class IndexedDict(OrderedDict):
    def __init__(self,*args):
        OrderedDict.__init__(self,args)

    def index(self,i):
        keys=list(self.keys())
        try:
            return keys[i],self[keys[i]]
        except IndexError:
            raise IndexError("Out of bounds access in IndexedDict()")
