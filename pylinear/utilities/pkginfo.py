from pkg_resources import get_distribution
from collections import OrderedDict

''' Simple thing to get return an OrderedDict() with the package's metadata '''




def pkginfo(package):

    # return the meta data as a list
    pkg=get_distribution(package)       
    metadata=pkg._get_metadata(pkg.PKG_INFO)

    # repackage as an OrderedDict()
    data=OrderedDict()
    for m in metadata:
        # parse the line
        q=m.split(': ')
        q=[qq.split(' :')[0] for qq in q]

        # get the keyword,value pair
        key,value=q[0].lower(),q[1:]
        if len(value)==1:
            value=value[0]
        data[key]=value
    return data
