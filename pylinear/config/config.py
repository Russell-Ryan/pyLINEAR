import ruamel.yaml as yaml

class Config(object):
    def __init__(self,*args,conffile=None):
        """ A class to hold YML configuration data.

        This is meant to look like a dictionary to user, and will contain
        any comments in the loaded YAML file.

            >>> cnf=Config(*args,conffile=None)

        """

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
        """ Load a YAML config file.

        Uses the ruamel.yaml class to store the comments.
        
        Parameters
        ----------
        conffile : str
            The full path for a YAML config file.

        Returns
        -------
        nothing, but loads into the object.
        """
        
        try:
            with open(conffile,'r') as f:
                self.conf=self.yaml.load(f)
        except:
            raise FileNotFoundError("{} not found.".format(conffile))
            
        self.conffile=conffile
            
        
    def items(self):
        """ Return the dictionary items.

        Just emulates the dictionary functionality.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        
        return self.conf.items()


    def _flatten(self,dic,old='',sep='-'):
        out=[]
        for k,v in dic.items():
            if old == '':
                new=k
            else:
                new=old+sep+k
            if isinstance(v,dict):
                out.extend(self._flatten(v,old=new,sep=sep))
            else:
                if k in dic.ca.items:
                    val=dic.ca.items[k][2]
                    if val is not None:
                        comment=val.value[2:].strip()
                    else:
                        comment=''
                else:
                    comment=''
                    
                out.append((new,v,comment))
        return out
                           
    def flatten(self):
        return self._flatten(self.conf)

    
    #def gattr(self,keys):
    #    data=self.conf
    #    for key in keys:
    #        try:
    #            data=data[key]
    #        except:
    #            return None
    #    return data
    #
    #def sattr(self,keys,value):
    #    
    #    data=self.conf
    #
    #    #self.conf['modules']['extraction']['lsqr']['atol']=value
    #    f='self.conf["'+'"]["'.join(keys)+'"]='+str(value)
    #    q=exec(f)
                
        
    def __iter__(self):
        self.yaml.dump(self.conf,self.stream)
        string=self.stream.getvalue()
        strings=string.split('\n')
        for string in strings:
            yield string
        

    def __str__(self):
        self.yaml.dump(self.conf,self.stream)
        return self.stream.getvalue()

    def __contains__(self,k):
        return k in self.conf

    def __setitem__(self,k,v):
        self.conf[k]=v

    
    def __getitem__(self,key):
        try:
            value=self.conf[key]
        except:
            raise KeyError('"{}" not found.'.format(key))

        if isinstance(value,dict):
            out=Config(value)
            out.conffile=self.conffile
        else:
            out=value            
        return out        

        
    def write(self,filename):
        with open(filename,'w') as f:
            self.yaml.dump(self.conf,f)

    
            
if __name__=='__main__':
    x=Config(conffile='defaults.yml')

    #print(x.gattr(['modules','extraction','lsqr','atol']))
    #x.sattr(['modules','extraction','lsqr','atol'],2)
    #print(x.gattr(['modules','extraction','lsqr','atol']))
