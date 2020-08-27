from .h5table import H5Table

from .ddt import DDT
from .odt import ODT
from .ovt import OVT
from .omt import OMT
from .pdt import PDT

# global settings for the compression of HDF5 files
compargs={'compression':'gzip','compression_opts':9}
