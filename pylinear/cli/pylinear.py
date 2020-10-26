import pylinear
import argparse as ap
import os


# custom class to format argparse
class CustomFormatterClass(ap.ArgumentDefaultsHelpFormatter,
                           ap.MetavarTypeHelpFormatter):
    pass


#def readable(value):
#    if os.path.isfile(value):
#        if os.access(value,os.R_OK):
#            return value
#        else:
#            raise ap.ArgumentTypeError("File is not readable")
#    else:
#        raise ap.ArgumentTypeError("File does not exist")
#
#def writeable(value):
#    path=os.path.dirname(os.path.abspath(value))
#    if os.access(path,os.W_OK):
#        return value
#    else:
#        raise ap.ArgumentTypeError("Path is not writeable")

    
def parse_args():
    config=pylinear.Config()
    
    parser=ap.ArgumentParser(description='''{} v{}: Linear Extraction 
                             and Simulation of Slitless 
                             Spectroscopy'''.format(pylinear.__code__,
                                                    pylinear.__version__),
                             epilog='Reference: {}'.format(pylinear.__ref__),
                             formatter_class=CustomFormatterClass)


    
    parser.add_argument('conffile', nargs='?',help='Configuration File',
                        type=str)#pylinear.utilities.argparse.readable)
                        
    
    modesgrp = parser.add_argument_group('Running Modes')
    modesgrp.add_argument('-e','--extract',action='store_true',
                          help='Extract grism image(s)')

    modesgrp.add_argument('-f','--fluxcube',action='store_true',
                          help='Extract IFU-like flux cube')
    
    modesgrp.add_argument('-s','--simulate',action='store_true',
                          help='Simulate grism image(s)')
    
    modesgrp.add_argument('-t','--tabulate',action='store_true',
                          help='Tabulate grism image(s)')

    modesgrp.add_argument('-d','--dump',nargs='?',
                          help='Dump the default configuration',
                          type=pylinear.utilities.argparse.writeable,
                          const='{}.cfg'.format(pylinear.__code__.lower()))
                          

    # put the config in the argparse
    confgrp = parser.add_argument_group('Configuration Settings')
    config.update_argparse(confgrp)

    # get the arguments as a dictionary
    args=vars(parser.parse_args())

    # update the config with the command line results
    config.update_from_commandline(args)

    # if config file was specified, then use that to over-ride things
    conffile=args.get('conffile',None)
    if isinstance(conffile,str) and os.path.isfile(conffile):
        try:
            config.load_ascii(conffile)
        except:
            print('[warn]Invalid configuration file')
    
    return args
    
def extract():
    print('[info]Running pyLINEAR Extract')
    
    conf=pylinear.Config()

    # Step 1.  Load sources
    sources=pylinear.source.SourceCollection(conf['segfile'],conf['obslst'],
                                             maglim=conf['maglim'],
                                             detindex=conf['detindex'])

        
    # get the detection filter
    #detfilt=sources.obscat.detband.filt

    # step 2.  load grism images for simulation
    grisms=pylinear.grism.GrismCollection(conf['imglst'],observed=True)
    
    # step 2b. get the default extraction settings and set to the sources
    default_extract=grisms.get_default_extraction()
    sources.update_extraction_parameters(**default_extract)
    
    
    # step 3a.  compute the pixel tables
    tabulate=pylinear.modules.Tabulate('pdt',remake=conf['remake'],
                                       path=conf['path'],nsub=conf['nsub'],
                                       ncpu=conf['ncpu'])
    pdtnames=[tabulate.run(grisms,sources,beam) for beam in conf['beams']]

    # step 3b. compute the masks
    tabulate.ttype='omt'
    tabulate.nsub=1
    omtnames=[tabulate.run(grisms,sources,beam) for beam in conf['mskbeams']]

    # get the parse file
    grpfile=None if conf['grpfile']=='' else conf.get('grpfile',None)

    
    # step 4.  do the 1d extraction
    pylinear.modules.extract.extract1d(grisms,sources,conf['beams'],
                                       conf['logdamp'],conf['method'],
                                       conf['root'],conf['path'],
                                       inverter=conf['inverter'],
                                       mskbeams=conf['mskbeams'],
                                       usehdf5=conf['usehdf5'],
                                       matrix_path=conf['matpath'],
                                       grpfile=grpfile,group=conf['group'],
                                       ncpu=conf['ncpu'])
def extract_fluxcube():
    print('[info]Running pyLINEAR Extract_Fluxcube')
    conf=pylinear.Config()

    # Step 1.  Load sources
    sources=pylinear.source.SourceCollection(conf['segfile'],conf['obslst'],
                                             detindex=conf['detindex'],
                                             maglim=conf['maglim'],
                                             cubeid=conf['cubeid'])
        
    
    # get the detection filter
    #detfilt=sources.obscat.detband.filt

    # step 2.  load grism images for simulation
    grisms=pylinear.grism.GrismCollection(conf['imglst'],observed=True)

    # step 2b. get the default extraction settings and set to the sources
    default_extract=grisms.get_default_extraction()
    sources.update_extraction_parameters(*default_extract)

    
    # step 3a.  compute the pixel tables
    tabulate=pylinear.modules.Tabulate('pdt',remake=conf['remake'],
                                       path=conf['path'],nsub=conf['nsub'],
                                       ncpu=conf['ncpu'])
    pdtnames=[tabulate.run(grisms,sources,beam) for beam in conf['beams']]

    # step 3b. compute the masks
    tabulate.ttype='omt'
    tabulate.nsub=1
    omtnames=[tabulate.run(grisms,sources,beam) for beam in conf['mskbeams']]

    # step 4.  do the 1d extraction
    pylinear.modules.extract.extract2d(grisms,sources,conf['beams'],
                                       conf['logdamp'],conf['method'],
                                       conf['root'],conf['path'],
                                       inverter=conf['inverter'],
                                       mskbeams=conf['mskbeams'])

def simulate():
    print('[info]Running pyLINEAR Simulate')
    conf=pylinear.Config()
    
    # Step 1.  Load sources
    sources=pylinear.source.SourceCollection(conf['segfile'],conf['obslst'],
                                             maglim=conf['maglim'],
                                             detindex=conf['detindex'])

    # get the detection filter
    #detfilt=sources.obscat.detband.filt
        
    # step 2.  load grism images for simulation
    grisms=pylinear.grism.GrismCollection(conf['wcslst'],observed=False)
    
    # step 3.  compute the pixel tables
    tabulate=pylinear.modules.Tabulate('pdt',remake=conf['remake'],
                                       path=conf['path'],nsub=conf['nsub'],
                                       ncpu=conf['ncpu'])
    pdtnames=[tabulate.run(grisms,sources,beam) for beam in conf['beams']]
    
    # step 4.  run a simulation
    simulate=pylinear.modules.Simulate(conf['sedlst'],path=conf['path'],
                                       ncpu=conf['ncpu'],gzip=conf['gzip'])
    filenames=[simulate.run(grisms,sources,beam) for beam in conf['beams']]


def tabulate():
    print('[info]Running pyLINEAR Tabulate')

    conf=pylinear.Config()
    
    # Step 1.  Load sources
    sources=pylinear.source.SourceCollection(conf['segfile'],conf['obslst'],
                                             maglim=conf['maglim'],
                                             detindex=conf['detindex'])
    # get the detection filter
    #detfilt=sources.obscat.detband.filt
        
    # step 2.  load grism images for simulation
    grisms=pylinear.grism.GrismCollection(conf['wcslst'],observed=False)


    print(conf['beams'])
    # step 3a.  compute the pixel tables
    tabulate=pylinear.modules.Tabulate('pdt',remake=conf['remake'],
                                       path=conf['path'],nsub=conf['nsub'],
                                       ncpu=conf['ncpu'])
    pdtnames=[tabulate.run(grisms,sources,beam) for beam in conf['beams']]

    # step 3b.
    tabulate.nsub=1
    tabulate.ttype='omt'
    omtnames=[tabulate.run(grisms,sources,beam) for beam in conf['mskbeams']]
    

def dump_config(filename):
    config=pylinear.Config()
    config.write_ascii(filename)

def main():    
    
    # get the inputs
    args = parse_args()

    
    # test if there were steps to run
    run=any(v is not None and v!=False for v in args.values())
    if not run:
        print('[info]pyLINEAR has nothing to do.')
        return 1

    # could adjust log settings with:
    #print(pylinear.log)
    

    conf=pylinear.Config()
    
    # print the config
    print(conf)
    for k,v in args.items():
        if k == 'extract' and v:
            extract()
        elif k =='fluxcube' and v:
            extract_fluxcube()
        elif k =='simulate' and v:
            simulate()
        elif k =='tabulate' and v:
            tabulate()
        elif k=='dump' and isinstance(v,str):
            dump_config(v)
        else:
            pass

    
if __name__=='__main__':
    main()
