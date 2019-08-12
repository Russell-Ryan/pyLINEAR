class Base(object):
    def __init__(self):
        pass

    def __str__(self):
        return '{} for {}'.format(self.ttype,self.name)

    def notFound(self):
        #print("[warn]{} for {} not found.".format(self.ttype,self.name))
        pass
    
    @property
    def ttype(self):
        return self.__class__.__name__
