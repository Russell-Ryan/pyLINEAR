from .info import __author__,__code__,__email__,__ref__,__version__
#from .cli import pylinear
from . import modules
from . import source
from . import grism
from . import utilities
from .config import Config
import os

try:
    x=os.environ['PYLINEAR_CONFIG']
except:
    raise RuntimeError('Must specify "PYLINEAR_CONFIG" in the environment')


for key in ['PYLINEAR_CONFIG']:
    if key not in os.environ:        
        print("Unable to setup pyLINEAR: must set '{}'".format(key))
        exit(1)



import colorlog
log=colorlog.ColorLog(root='{}_v{}'.format(__code__,__version__))
