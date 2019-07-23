class Base(object):
    def __init__(self):
        pass

    def __str__(self):
        return '{} for {}'.format(self.ttype,self.name)

    @property
    def ttype(self):
        return self.__class__.__name__
