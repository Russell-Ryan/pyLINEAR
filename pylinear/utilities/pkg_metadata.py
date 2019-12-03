import pkg_resources
import re

''' A simple script to get the meta data for a package by reading the EGGs. '''

def pkg_metadata(name):
    ''' return the meta data as a dict

    This will append like keywords.  For example, you may have multiple 
    `Classifiers`, which will be appended into a list.  All values of the 
    dictionary will be strings.

    Parameters
    ----------
    name : str 
        the name of the package

    Returns
    -------
    meta : dict
        dictionary of the package data
    '''


    meta={}     # output metadata struct

    # a generator of the meta data
    d=pkg_resources.get_distribution(name)
    for m in d._get_metadata(d.PKG_INFO):       

        # split on a ':' but not on '::'
        spl=re.split('(?<!:):(?!:)\s',m)
        if len(spl)==2:
            # check for a tuple spliting
            key,value=spl[0],spl[1]
            if key in meta:
                # if the key already exists, then append it as a list
                if isinstance(meta[key],list):
                    meta[key].append(value)
                else:
                    meta[key]=[meta[key],value]
            else:
                # add the keyword to the dictionary
                meta[key]=value
            
    
    return meta
    


if __name__=='__main__':
    ''' Simple testing script '''
    m=pkg_metadata('pylinear')
    print(m)
