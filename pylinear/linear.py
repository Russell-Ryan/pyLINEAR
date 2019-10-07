import argparse as ap
import os
import shutil
import sys
import timeit
import numpy as np
import pkginfo

from . import config
from . import source
from . import modules
from .utilities import Logger





def splashMessage(conf,info):
    ''' display a splash message when the pipeline is called '''
    txt=['','', \
         '    '+info.description,\
         '', \
         '           by: '+info.author,\
         '', \
         '     citation: http://adsabs.harvard.edu/abs/2018PASP..130c4501R',
         '      version: '+info.version, \
         '      contact: '+info.author_email, \
         '']
    for t in txt:
        print(t)
    print(conf)



#def applyUser(defs,user):
#    for k,v in defs.items():
#        if isinstance(v,dict):
#            defs[k]=applyUser(v,user[k])
#        else: #if isinstance(v,(int,bool,str,float)) or (v is None):
#            if (k in user) and (defs[k]!=user[k]):
#                defs[k]=user[k]
#            
#    return defs#

#def applydefaults(user,defs):
#    for k in defs:
#        if isinstance(defs[k], dict): # if the current item is a dict,
#            applydefaults(user.setdefault(k, {}), defs[k])
#        else:
#            user.setdefault(k, defs[k])
#    return user


def updateDefaults(defs,user):
    out=defs.copy()
    for k,v in defs.items():
        if isinstance(v,dict):
            out[k]=updateDefaults(v,user[k])
        else:
            if k in user:
                out[k]=user[k]
                
    return out
    



def applyUser(user,defs):
    for k,v in defs.items():
        if isinstance(v,dict):
            user=applyUser(user[k],v)
        else:
            if k not in user:
                user[k]=defs[k]
    return user



def defaultConfig():
    ''' get the name of the default configuration file '''
    path=os.path.dirname(os.path.realpath(__file__))
    defsfile=os.path.join(path,'config','defaults.yml')

    return defsfile

    
def loadConfig(userfile,defs):
    ''' copy the default configuration file to the CWD '''
    
    # get the default configuration
    #defs=config.Config(conffile=defaultConfig())    # defaults
    
    # look to see if a config file was specified
    if userfile is not None and os.path.isfile(userfile):
        user=config.Config(conffile=userfile)
        defs.conf=updateDefaults(defs.conf,user.conf)
    defs.conffile=user.conffile

    return defs    

def runTime(t0,days=True,hours=True,minutes=True,seconds=True,lost=False):
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




def linearPipeline(conf):
    ''' call the linear pipelines '''

    # load sources (includes spectra) --- this also applies cuts for valid
    # sources (ie. too faint, too small, etc.)
    sources=source.Data(conf['sources'])
    
    # make a look-up table for the callable methods
    items=[(modules.simulate,'simulation'),
           (modules.extract,'extraction')]
    
    # call the modules
    [method(conf['modules'][key],sources) for (method,key) in items]
    
    

    # call the modules
    #modconf=conf['modules']    
    #modules.simulate(modconf['simulation'],sources)
    #modules.extract(modconf['extraction'],sources)
    #modules.cutout(modconf['cutout'],sources)
 


def main():
    ''' primary entry point to the code '''

    # get an initial time
    t0=timeit.default_timer()

    # get the pkg info
    #info=pkginfo(__package__)
    info=pkginfo.Installed(__package__)
    
    # read the defaults
    defs=config.Config(conffile=defaultConfig())
    #flat=defs.flatten()
    
    # parse the input     
    p=ap.ArgumentParser(description=info.name+': '+info.description,
                        formatter_class=ap.ArgumentDefaultsHelpFormatter)
    p.add_argument('config',help='YAML configuration file',nargs='?',\
                   default='linear.yml')
    p.add_argument('--logfile',help='output log file',nargs='?',\
                   default='linear.log')    #)#,metavar='linear.log')
    p.add_argument('-d','--dump',help='dump the default configuration',\
                   action='store_true')    

    #for f in flat:
    #    p.add_argument('--'+f[0],default=f[1],help=f[2],metavar='')
    args=p.parse_args()

    # must put in command-line arguments here


    
    # dump the configuration
    if args.dump:
        print(defs)
        return

    # open my custom logging utilities
    sys.stdout=Logger(info.name,logfile=args.logfile)
    
    # load the configuration with defaults
    conf=loadConfig(args.config,defs)
    
    # if we have a valid config:
    if conf is not None:
        # print a message
        splashMessage(conf,info)
    
        # call linear!
        linearPipeline(conf)


    # print an outro message
    print('[info]'+runTime(t0))
    

if __name__=='__main__':
    ''' a back-up entry point '''

    main()



    
