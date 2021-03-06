import argparse as ap
import os
import configparser
from astropy.io import fits
from .utilities import argparse as aputil
from .info import __version__,__code__,__ref__

# global comment symbol in output files
COMMENT='#'


def list_type(lst):
    ''' method to determine the datatype of a list 
    
    Parameters
    ----------
    lst : list
       A list whose sub-element datatypes will be returned
   
    Returns
    -------
    typ : type 
       the datatype of the first element of the list.

    '''
    if len(lst)==0:
        return str
    else:
        return type(lst[0])


    
class Keyword(object):
    ''' Class to hold a keyword, value, comment triplet 

    Parameters
    ----------
    key : str
       A header keyword name.
    val : Any
       A header keyword value.
    com : str
       A header keyword comment card

    Optional Parameters
    -------------------
    choices : list (default: None)
       A string list of possible values 

    read : boolean (default: False)
       A flag that the keyword should be readable

    write : boolean (default: False)
       A flag that the keyword should be writeable
    '''


    LEN = 36    # the length of an ascii formatted string
    
    def __init__(self,k,v,c,choices=None,read=False,write=False):
        self.keyword=k
        self.value=v
        self.default=v
        self.comment=c
        self.choices=choices
        self.access={'read':read,'write':write}
                
    def __str__(self):
        msg='\u001b[1m{0:8}\u001b[0m = {1:28} \ \u001b[33m{2}\u001b[0m'
        return msg.format(self.keyword,str(self.value),self.comment)
                          

    def reset(self):
        ''' Reset the keyword to the default value '''
        
        self.value=self.default

    def update_header(self,hdr,after=None):
        ''' Put the keyword into a FITS header 

        Parameters
        ----------
        hdr : `astropy.io.fits.header.Header`
           Header to update in place

        Optional Parameters
        -------------------
        after : str (default: None)
           Last existing header keyword
        '''
        
        
        if isinstance(self.value,(list,tuple)):
            val=str(self.value)[1:-1].replace(' ','')
            val=val.replace("'","").replace('"','')
            if len(val)==0:
                val=' '
        else:
            val=self.value

        hdr.set(self.keyword,val,self.comment,after=after)


        
    def to_argparse(self,parser):
        ''' Convert the keyword for argparse 
        
        Parameters
        ----------
        parser : `argparser.ArgumentParser`
           The parser object to update with this keyword.

        '''        
        if isinstance(self.value,bool):
            #parser.add_argument('--'+self.keyword,help=self.comment,
            #                    const=True,default=False,nargs='?',
            #                    type=boolean_type)
            parser.add_argument('--'+self.keyword,help=self.comment,
                                default=self.default,type=aputil.boolean)
                                
        elif isinstance(self.value,(list,tuple)):
            parser.add_argument('--'+self.keyword,default=self.default,
                                type=list_type(self.value),help=self.comment,
                                choices=self.choices,nargs='+')
        elif self.value is None:
            parser.add_argument('--'+self.keyword,default=self.default,
                                help=self.comment,choices=self.choices)
        elif isinstance(self.value,str):
            #if self.access['read']:
            #    parser.add_argument('--'+self.keyword,default=self.default,
            #                        type=aputil.readable,help=self.comment,
            #                        choices=self.choices)
            #elif self.access['write']:
            #    parser.add_argument('--'+self.keyword,default=self.default,
            #                        type=aputil.writeable,help=self.comment,
            #                        choices=self.choices)
            #else:
            parser.add_argument('--'+self.keyword,default=self.default,
                                type=str,help=self.comment,
                                    choices=self.choices)
        else:
            parser.add_argument('--'+self.keyword,default=self.default,
                                type=type(self.value),help=self.comment,
                                choices=self.choices)
    def as_ascii(self):
        ''' Convert the keyword, value, comment to an ascii format 

        Parameters
        ----------
        None

        Returns
        -------
        formatted_str : str
           A formatted string of the keyword,value,comment triplet
        '''

        
        if isinstance(self.value,list):
            val=str(self.value)[1:-1].replace(' ','')
            val=val.replace("'","").replace('"','')
        elif isinstance(self.value,bool):
            val='yes' if self.value else 'no'
        elif self.value is None:
            val=''
        else:
            val=str(self.value)
        
        val=val.ljust(self.LEN-len(self.keyword))


        return '{0} {1} {2}'.format(val,COMMENT,self.comment)


    

class Config(object):
    ''' A singleton class to hold the configuration

    Optional Parameters
    -------------------
    parser = `argparser.ArgumentParser` (default: None)
        
    
    '''
    



    _instance=None    # To make this a singleton

    # these variables specify which keywords belong to which modules
    _extract1d=['segfile','obslst','imglst','detindex','path','remake',
                'inverter',
                'method','logdamp','usehdf5','hdf5file','ncpu','nsub']
    

    # will add noise and background properties
    _simulate=['segfile','obslst','imglst','wcslst','wcstype','tables',
               'remake','beams']
    _tabulate=['segfile','obslst','imglst','tables','remake','beams',
               'mskbeams']

    

    
    def __new__(cls,parser=None):
        if cls._instance is None:
            cls._instance=super(Config,cls).__new__(cls)


            # set the defaults for pyLINEAR here:
            cls.cfg={}
            cls.cfg['segfile']=Keyword('segfile','seg.fits','full path to the segmentation image',read=True)
            cls.cfg['obslst']=Keyword('obslst','obs.lst','list of direct images',read=True)
            cls.cfg['imglst']=Keyword('imglst','flt.lst','list of grism images',read=True)
            cls.cfg['maglim']=Keyword('maglim',26.,'magnitude limit of the catalog')
            cls.cfg['detindex']=Keyword('detindex',0,'image for detection weights')
            cls.cfg['sedlst']=Keyword('sedlst','sed.lst','list of SEDs',read=True)
            cls.cfg['wcslst']=Keyword('wcslst','wcs.lst','list of WCS data',read=True)
            cls.cfg['wcstype']=Keyword('wcstype','wcs','where to take the WCS from',choices=['flt','wcs'])
            cls.cfg['path']=Keyword('path','tables','relative path to where tables',write=True)
            cls.cfg['gzip']=Keyword('gzip',True,'gzip output products')
            cls.cfg['remake']=Keyword('remake',False,'flag to force remaking the tables')
            cls.cfg['inverter']=Keyword('inverter','lsqr','method for inverting the matrix',choices=['lsqr','lsmr'])
            cls.cfg['method']=Keyword('method','golden','method for optimizing regularization',choices=['grid','golden','single'])
            cls.cfg['logdamp']=Keyword('logdamp',[-5.,-1.,0.1],'log-damping values')
            cls.cfg['beams']=Keyword('beams',['+1'],'beams to process')
            cls.cfg['mskbeams']=Keyword('mskbeams',[],'beams to mask in extraction')
            cls.cfg['group']=Keyword('group',True,'flag to group objects before extracting')
            cls.cfg['grpfile']=Keyword('grpfile','','group file to use')
            cls.cfg['root']=Keyword('root','pylinear','output files start with this name')
            #cls.cfg['wrmatrix']=Keyword('wrmatrix',True,'flag to write the HDF5 matrix files')
            cls.cfg['usehdf5']=Keyword('usehdf5',False,'flag to load from HDF5 matrix files')
            cls.cfg['matpath']=Keyword('matpath','matrices','Path where matrices are stored')
            cls.cfg['cubeid']=Keyword('cubeid',1,'SegID for flux-cube extraction')
            
            # things that probably shouldn't be fiddled with
            cls.cfg['ncpu']=Keyword('ncpu',0,'number of CPU to use (0=optimize)')
            cls.cfg['nsub']=Keyword('nsub',10,'wavelength subsampling rate')

            
        return cls._instance

    def __getitem__(self,k):
        return self.cfg[k].value

    def __setitem__(self,k,v):
        self.cfg[k].value=v

    def __getattr__(self,k):
        return self.cfg[k].value

    def __setattr__(self,k,v):
        self.cfg[k].value=v

    def __iter__(self):
        yield from self.cfg.items()

    def __contains__(self,k):
        return k in self.cfg
        
        
    def __str__(self):
        out=[str(v) for v in self.cfg.values()]
        out.insert(0,'\n\u001b[4m{} configuration:\u001b[0m\n'.format(__code__))
        return '\n'.join(out)

    def reset(self):
        ''' Reset all keyword values to their defaults'''

        for k,v in self:
            v.reset()


    def update_argparse(self,parser):
        ''' add these keyword to an existing argparse object

        Parameters
        ----------
        parser : `argparse.ArgumentParser`
           command-line parser to update
        '''

        for v in self.cfg.values():
            v.to_argparse(parser)

    def update_from_commandline(self,conf,remove=True):        
        

        
        # update config
        for k in list(conf.keys()):
            if k in self:
                self[k]=conf[k]
                if remove:
                    conf.pop(k)
            
    @classmethod
    def from_commandline(cls,parser):
        ''' Create a new config object from the command-line arguments '''

        
        cls=cls.__new__(cls)
    
        # put the items in the parser
        cls.update_argparse(parser)
    
        # parse the command-line
        args=vars(parser.parse_args())
        
        # update from the parser
        cls.update_from_commandline(args,remove=False)
        
        return cls

            
    def update_header(self,hdr):

        # get the last keyword
        keys=list(hdr.keys())
        if len(keys)==0:
            last=None
        else:
            last=keys[-1]
        after=last


        first=None
        for k,v in self:
            v.update_header(hdr,after=after)
            after=k
            if not first:
                first=k
                
        hdr.set('',value='',before=first)
        hdr.set('',value='      / Configuration Settings',before=first)
        hdr.set('',value='',before=first)

    @classmethod
    def from_header(cls,hdr):
        cls=cls.__new__(cls)
        for k,v in cls:
            if k in hdr:
                if isinstance(v.value,(list,tuple)):
                    if len(hdr[k])==0:
                        cls.cfg[k].value=[]
                    else:
                        lst=hdr[k].split(',')
                        typ=list_type(v.value)
                        cls.cfg[k].value=[typ(el) for el in lst]
                else:
                    cls.cfg[k].value=hdr[k]
            else:
                pass
        return cls
            
    def write_ascii(self,filename):
        config=configparser.ConfigParser(inline_comment_prefixes=COMMENT)
        config[__code__]={k:v.as_ascii() for k,v in self}
        with open(filename,'w') as fp:
            msg='{} Config file for {} v{}'
            print(msg.format(COMMENT,__code__,__version__),file=fp)
            config.write(fp)


    def load_ascii(self,filename):
        config = configparser.ConfigParser(inline_comment_prefixes=COMMENT)
        config.read(filename)
        for k,v in self:
            if isinstance(v.value,(list,tuple)):
                if len(config[__code__][k])==0:
                    self.cfg[k].value=[]
                else:
                    lst=config[__code__][k].split(',')
                    typ=list_type(v.value)
                    self.cfg[k].value=[typ(el) for el in lst]
            elif isinstance(v.value,bool):
                self.cfg[k].value=config[__code__].getboolean(k)
            elif isinstance(v.value,int):
                self.cfg[k].value=config[__code__].getint(k)
            elif isinstance(v.value,float):
                self.cfg[k].value=config[__code__].getfloat(k)
            else:
                if config[__code__][k]=='':
                    self.cfg[k].value=None
                else:
                    self.cfg[k].value=config[__code__][k]
    @classmethod
    def from_ascii(cls,filename):
        cls=cls.__new__(cls)
        config = configparser.ConfigParser(inline_comment_prefixes=COMMENT)
        config.read(filename)
        for k,v in cls:
            if isinstance(v.value,(list,tuple)):
                if len(config[__code__][k])==0:
                    cls.cfg[k].value=[]
                else:
                    lst=config[__code__][k].split(',')
                    typ=list_type(v.value)
                    cls.cfg[k].value=[typ(el) for el in lst]
            elif isinstance(v.value,bool):
                cls.cfg[k].value=config[__code__].getboolean(k)
            elif isinstance(v.value,int):
                cls.cfg[k].value=config[__code__].getint(k)
            elif isinstance(v.value,float):
                cls.cfg[k].value=config[__code__].getfloat(k)
            else:
                if config[__code__][k]=='':
                    cls.cfg[k].value=None
                else:
                    cls.cfg[k].value=config[__code__][k]
        return cls
            
    
def test():
    conf=Config().from_ascii('test.cfg')
    print(conf['segfile'])




class CustomFormatter(ap.ArgumentDefaultsHelpFormatter,
                      ap.MetavarTypeHelpFormatter):
    ''' Customized formatter class for argparse '''
    pass
    
    #def add_usage(self,usage,actions,groups,prefix=None):
    #return super(CustomFormatter,self).add_usage(usage,actions,groups,prefix)
    
 
if __name__=='__main__':

    
    #parser=ap.ArgumentParser(description='''{} v{}: Linear Extraction 
    #                         and Simulation of Slitless 
    #                         Spectroscopy'''.format(__code__,__version__),
    #                         epilog='Reference: {}'.format(__ref__),
    #                         formatter_class=CustomFormatter)

    
    #a=Config(parser=True)

    parser=ap.ArgumentParser(description='''{} v{}: Linear Extraction 
                                 and Simulation of Slitless 
                                 Spectroscopy'''.format(__code__,__version__),
                             epilog='Reference: {}'.format(__ref__),
                             formatter_class=CustomFormatter)        
  
    a=Config.from_commandline(parser)
    
    #config = configparser.ConfigParser(inline_comment_prefixes=COMMENT)
    #config.sections()
    a.segfile='q.fits'


    a.write_ascii('test.cfg')

    
    test()

    a.from_ascii('test.cfg')
    print(a)
    
    hdr=fits.Header()
    a.update_header(hdr)

    a.segfile='t.fits'
    print(a)
    a.reset()
    

    b=Config.from_header(hdr)
    
    print(b)
    b.reset()
    print(b)
