from .. import info
from datetime import datetime

#import pkg_resources

DISCLAIMER=["This file was created by pyLINEAR, which was written by Russell",
            "Ryan (rryan@stsci.edu) and is based on the LINEAR algorithm.  If",
            "this is useful, then we kindly ask you reference that work:",
            "https://ui.adsabs.harvard.edu/abs/2018PASP..130c4501R/abstract",
            "",
            "The pyLINEAR source code is distributed under the MIT License."]


#def get_pkg_license(pkgname):
#    """
#     Given a package reference (as from requirements.txt),
#     return license listed in package metadata.
#     NOTE: This function does no error checking and is for
#     demonstration purposes only.
#     """
#    pkgs = pkg_resources.require(pkgname)
#    pkg = pkgs[0]
#    for line in pkg.get_metadata_lines('PKG-INFO'):
#        (k, v) = line.split(': ', 1)
#        if k == "License":
#            return v
#    return None


def add_stanza(hdr,label,**kwargs):
    hdr.set('',value='',**kwargs)
    hdr.set('',value='      / {}'.format(label),**kwargs)
    hdr.set('',value='',**kwargs)


def get_last_keyword(hdr):
    k=None
    for k in hdr.keys():
        pass
    return k



def add_software_log(hdr,runtime=None):
    if isinstance(runtime,float):
        days,rem=divmod(runtime,24*60*60)
        hours,rem=divmod(rem,60*60)
        mins,secs=divmod(rem,60)
        labels=(int(days),int(hours),int(mins),int(secs))
        runtime='{0}d{1:02d}h{2:02d}m{3:02d}s'.format(*labels)

       
    # get a timestamp
    now=datetime.now()
    
    keys=list(hdr.keys())
    if len(keys)>0:
        after=keys[-1]
    else:
        after=None

    hdr.set('VERSION',value=info.__version__,after=after,
            comment='pyLINEAR version number')
    hdr.set('MADEON',value=now.strftime("%Y-%m-%d"),after='VERSION',
            comment='creation date (YYYY-MM-DD)')
    hdr.set('MADEAT',value=now.strftime("%H:%M:%S"),after='MADEON',
            comment='time file was written (hh:mm:ss)')
    if runtime:
        hdr.set('RUNTIME',value=runtime,after='MADEAT',
                comment='time to compute (dd:hh:mm:ss)')
    hdr.set('',value='',before='VERSION')
    hdr.set('',value='      / Software Log',before='VERSION')
    hdr.set('',value='',before='VERSION')

    

def add_disclaimer(hdr):
    # put some Comments into the file.  Force them to be at the end.
    
    keys=list(hdr.keys())
    if len(keys)==0:
        after=None
    else:
        after=keys[-1]
        #after=list(hdr.keys())[-1]   # the last keyword
    
    for disclaimer in reversed(DISCLAIMER):
        hdr.add_comment(disclaimer,after=after)
    hdr.set('',value='',after=after)
    hdr.set('',value='      / pyLINEAR Disclaimer',after=after)
    hdr.set('',value='',after=after)
