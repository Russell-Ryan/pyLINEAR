import argparse as ap
import os
import shutil
import sys
import timeit
import numpy as np
#import pkginfo


from . import config
from . import source
from . import modules
from .utilities import Logger,pkg_metadata


def splashMessage(conf,info):
    ''' display a splash message when the pipeline is called '''
    txt=['','', \
         '    '+info['Summary'],
         '', \
         '           by: '+info['Author'],
         '', \
         '     citation: http://adsabs.harvard.edu/abs/2018PASP..130c4501R',
         '      version: '+info['Version'],
         '      contact: '+info['Author-email'], \
         '']
    for t in txt:
        print(t)
    print(conf)


def updateDefaults(defs,user):
    out=defs.copy()
    for k,v in defs.items():
        if isinstance(v,dict):
            out[k]=updateDefaults(v,user[k])
        else:
            if k in user:
                out[k]=user[k]
                
    return out
    


def defaultConfigFile():
    ''' get the name of the default configuration file '''
    filename=os.path.join('config','defaults.yml')

    #import pkg_resources as pr
    #filename=pr.resource_filename(__package__,filename)
        
    path=os.path.dirname(os.path.realpath(__file__))
    defsfile=os.path.join(path,filename)

    return defsfile

    
def loadConfig(userfile,defs):
    ''' copy the default configuration file to the CWD '''
        
    # look to see if a config file was specified
    if userfile is not None and os.path.isfile(userfile):
        user=config.Config(conffile=userfile)
        defs.conf=updateDefaults(defs.conf,user.conf)
        defs.conffile=user.conffile

    return defs    

def printRunTime(t0,days=True,hours=True,minutes=True,seconds=True,lost=False):
    ''' compute the run time in a special string format '''
    t1=timeit.default_timer()
    
    nday,rem=divmod(t1-t0,24*60*60)
    nhour,rem=divmod(rem,60*60)
    nminute,seconds=divmod(rem,60)
    nsecond=np.floor(seconds)
    lostTime=seconds-nsecond
    msg='runtime: '
    if days:
        msg=msg+' {:>2}d'.format(nday)
    if hours:
        msg=msg+' {:0>2}h'.format(nhour)
    if minutes:
        msg=msg+' {:0>2}m'.format(nminute)
    if seconds:
        msg=msg+' {:0>2}s'.format(nsecond)
    if lost:
        msg=msg+' {}'.format(lostTime)
    return msg




def runLinear(conf):
    ''' call the linear pipelines '''

    # load sources (includes spectra) --- this also applies cuts for valid
    # sources (ie. too faint, too small, etc.)
    sources=source.Data(conf['sources'])
    
    # make a look-up table for the callable methods
    mods=[(modules.simulate,'simulation'),
          (modules.extract,'extraction'),
          (modules.cutout,'cutout')]
    
    # call the modules
    for (method,key) in mods:
        method(conf['modules'][key],sources)


def parseCommandLineArgs(info):
    
    # parse the input     
    p=ap.ArgumentParser(description=info['Name']+': '+info['Summary'],
                        formatter_class=ap.ArgumentDefaultsHelpFormatter)
    p.add_argument('config',help='YAML configuration file',nargs='?',\
                   default='{}.yml'.format(__package__))
    p.add_argument('--logfile',help='output log file',nargs='?',\
                   default='{}.log'.format(__package__))
    p.add_argument('-d','--dump',help='dump the default configuration',\
                   action='store_true')
    
    # update with the argparser with the 
    #for flat in defs.flatten():
    #    p.add_argument('--'+flat[0],default=flat[1],help=flat[2],metavar='')

    # put the command-line results into the defs

    # parse the args
    args=p.parse_args()

    # dump the configuration
    if args.dump:
        defs=config.Config(conffile=defaultConfigFile())
        print(defs)
        exit(0)


    return args


def main():
    ''' entry point for command-line '''


    # ignore the AstropyWarnings.  
    import warnings
    from astropy.utils.exceptions import AstropyWarning
    warnings.simplefilter('ignore', category=AstropyWarning)
    
    # get an initial time
    t0=timeit.default_timer()

    # get the pkg info
    #info=pkginfo.Installed(__package__)
    info=pkg_metadata(__package__)

    
    # get the command-line Arguments    
    args=parseCommandLineArgs(info)
            
    # open my custom logging utilities
    sys.stdout=Logger(info['Name'],logfile=args.logfile)
    

    # load the configuration with defaults
    conf=loadConfig(args.config,config.Config(conffile=defaultConfigFile()))
    
    # if we have a valid config:
    if conf is not None:
        # print a message
        splashMessage(conf,info)

        # call linear!
        runLinear(conf)


    # print an outro message
    print('[info]'+printRunTime(t0))
    

if __name__=='__main__':
    ''' a back-up entry point '''

    main()



    
