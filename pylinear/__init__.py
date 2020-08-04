from .info import __author__,__code__,__email__,__ref__,__version__
#from .cli import pylinear
from . import modules
from . import source
from . import grism
from . import utilities
from .config import Config
import os



import colorlog
log=colorlog.ColorLog(root='{}_v{}'.format(__code__,__version__))



try:
    x=os.environ['PYLINEAR_CONFIG']
except:
    #raise RuntimeError("You must specify 'PYLINEAR_CONFIG' in the environment")
    print('[warn]You must specify pylinear_config')



