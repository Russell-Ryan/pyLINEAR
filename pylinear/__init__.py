from .info import __author__,__code__,__email__,__ref__,__version__
from . import modules
from . import source
from . import grism
from . import utilities
from .config import Config
import os


# set the logging utility
import colorlog
log=colorlog.ColorLog(root='{}_v{}'.format(__code__,__version__))

# to support the logging utility
import tqdm
import inspect
builtin_print=print
def pylinear_print(*args,**kwargs):
    try:
        tqdm.tqdm.write(*args,**kwargs)
    except:
        builtin_print(*args,**kwargs)
inspect.builtins.print=pylinear_print  # need to do this :(


# check that the configuration data is present
if 'PYLINEAR_CONFIG' not in os.environ:
    raise RuntimeError("You must specify 'PYLINEAR_CONFIG' in the environment")
    



