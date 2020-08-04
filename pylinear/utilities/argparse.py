import argparse as ap
import os


def readable(value):
    
    if os.path.isfile(value):
        if os.access(value,os.R_OK):
            return value
        else:
            raise ap.ArgumentTypeError("File is not readable")
    else:
        raise ap.ArgumentTypeError("File does not exist")

def writeable(value):
    path=os.path.dirname(os.path.abspath(value))
    if os.access(path,os.W_OK):
        return value
    else:
        raise ap.ArgumentTypeError("Path is not writeable")

    
def boolean(val):
    if isinstance(val,bool):
        return val
    if val.lower() in ('yes','true','t','y','1'):
        return True
    elif val.lower() in ('no','false','f','n','0'):
        return False
    else:
        raise ap.ArgumentTypeError('Boolean value expected.')
