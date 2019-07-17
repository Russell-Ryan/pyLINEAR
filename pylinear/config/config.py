import ruamel.yaml as yaml

class Config(object):
    def __init__(self,*args,conffile=None):

        # create the reader
        def represent_none(yml,data):
            return yml.represent_scalar(u'tag:yaml.org,2002:null', u'Null')
        self.yaml=yaml.YAML()
        self.yaml.Representer.add_representer(type(None),represent_none)
        self.yaml.boolean_representation = ['False', 'True']
        self.yaml.preserve_quotes=False
        
        # create this for access later
        self.stream=yaml.compat.StringIO()
                
        # set the value
        if len(args)==1 and isinstance(args[0],dict):
            self.conf=args[0]
        else:
            self.conf=None
        
        # load from a file
        if conffile is not None:
            self.load(conffile)
            
            
    def load(self,conffile):

        try:
            with open(conffile,'r') as f:
                self.conf=self.yaml.load(f)

        except:
            raise FileNotFoundError("{} not found.".format(conffile))
            
        self.conffile=conffile
            

    def applyDefaults(self,defs):
        for k in defs:
            print(k)
            if isinstance(defs[k], dict): # if the current item is a dict,
                self.applyDefaults(user.setdefault(k, {}), defs[k])
            else:
                user.setdefault(k,defs[k])
        return user
    
    def __iter__(self):
        self.yaml.dump(self.conf,self.stream)
        string=self.stream.getvalue()
        strings=string.split('\n')
        for string in strings:
            yield string
        

    def __str__(self):
        self.yaml.dump(self.conf,self.stream)
        return self.stream.getvalue()

    
    def __getitem__(self,key):
        try:
            value=self.conf[key]
        except:
            raise KeyError('"{}" not found.'.format(key))

        if isinstance(value,dict):
            out=Config(value)
        else:
            out=value            
        return out        

        
    def write(self,filename):
        with open(filename,'w') as f:
            self.yaml.dump(self.conf,f)

    
            
if __name__=='__main__':
    x=Config(userfile='user.yml',defsfile='defs.yml')
    y=x['modules']
    logdamp=y['extraction']['logdamp']
    y.write('test.yml')
