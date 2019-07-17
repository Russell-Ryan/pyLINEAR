import subprocess



class GZipError(Exception):
    pass
        
def gzip(filename):
    r=subprocess.call(['gzip','-f',filename])
    if r != 0:
        raise GZipError("Cannot gzip: {} --- error: {}".format(filename,r))

def gunzip(filename):
    r=subprocess.call(['gunzip',filename])
    if r != 0:
        raise GZipError("Cannot gunzip: {} --- error: {}".format(filename,r))
