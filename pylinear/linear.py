import argparse
import os
import shutil
import sys
import timeit
import numpy as np


from .__init__ import __description__,__author__,__cite__,__version__,__email__
from . import config
from . import source
from . import modules
from .utilities import Logger


def splashMessage(conf):
    txt=['','', \
         '    '+__description__,\
         '', \
         '           by: '+__author__,\
         '', \
         '     citation: '+__cite__,\
         '      version: '+__version__, \
         '      contact: '+__email__, \
         '']
    for t in txt:
        print(t)
    print(conf)

def applyDefaults(user,defs):
    for k in defs:
        if isinstance(defs[k], dict): # if the current item is a dict,
            applydefaults(user.setdefault(k, {}), defs[k])
        else:
            user.setdefault(k, defs[k])
    return user
    

    
def getConfig():

    # get the default configuration
    path=os.path.dirname(os.path.realpath(__file__))
    defsfile=os.path.join(path,'config','defaults.yml')
    defs=config.Config(conffile=defsfile)
    

    # parse the inputs    
    p=argparse.ArgumentParser(description='LINEAR')
    p.add_argument('config',help='YAML configuration file',nargs='?',\
                   default='linear.yml')
    p.add_argument('-c','--copy',help='copy the default configuration to cwd',\
                   nargs='?')
    args=p.parse_args()

    # do we copy the default to a local directory
    if args.copy is not None:
        base,ext=os.path.splitext(args.copy)
        if ext not in ['.yml','yaml']:
            print('Warning, copying to a non-YAML type: {}'.format(args.copy))
        shutil.copyfile(defsfile,args.copy)

        return None


    # look to see if a config file was specified
    if args.config is not None and os.path.isfile(args.config):
        conf=config.Config(conffile=args.config)
        conf=applyDefaults(conf,defs)
    else:
        conf=defs


    return conf
    

def runTime(t0,t1,days=True,hours=True,minutes=True,seconds=True,lost=False):
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





def linearPipeline(conf):
    ''' call the linear pipelines '''

    # load sources (includes spectra)
    sources=source.Data(conf['sources'])

    
    # call the modules
    modconf=conf['modules']
    
    modules.simulate(modconf['simulation'],sources)
    modules.extract(modconf['extraction'],sources)
#    modules.cutout(modconf['cutout'],sources)
 


def main():
    # get an initial time
    t0=timeit.default_timer()

    # open my custom logging utilities
    sys.stdout=Logger('LINEAR',logfile='linear.log')

    # get the configuration
    conf=getConfig()
    if conf is not None:
        # print a message
        splashMessage(conf)
    
        # call linear!
        linearPipeline(conf)

    # get final time
    t1=timeit.default_timer()
    

    # print an outro message
    print(runTime(t0,t1))
    

if __name__=='__main__':
    main()



    
