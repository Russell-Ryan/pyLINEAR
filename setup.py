from setuptools import setup,find_packages
import os


PKG='pylinear'
AUTHOR='Russell Ryan'
info = {
    '__author__': AUTHOR,
    '__version__': '1.0',
    '__maintainer__': AUTHOR,
    '__author_email__': 'rryan@stsci.edu',
    '__license__': 'MIT',
    '__cite__': 'https://ui.adsabs.harvard.edu/abs/2018PASP..130c4501R/abstract',
    '__keywords__':'grism linear WFC3 HST',
    '__description__':'Linear Extraction and Simulation of Slitless Spectroscopy',
    '__credits__': AUTHOR
}

# Generate package metadata
#with open(os.path.join(PKG, 'info.py'), 'w+') as fp:
#    for k, v in info.items():
#        fp.write('{} = "{}"{}'.format(k, v, os.linesep))




#https://docs.python.org/2/distutils/setupscript.html
# call SETUP
setup(name=PKG,
      version=info['__version__'],
      author=info['__author__'],
      author_email=info['__author_email__'],
      keywords=info['__keywords__'],
      long_description=info['__description__'],
      maintainer=info['__maintainer__'],
      license=info['__license__'],
      #setup_requires=['wget'],
      install_requires=['numpy','astropy','numpy','h5axeconfig @ git+https://github.com/russell-ryan/h5axeconfig#egg=h5axeconfig','emcee','ruamel.yaml','pkginfo','shapely'],
      entry_points={'console_scripts':['pylinear=pylinear.linear:main']},
      classifiers=['Development Status :: 5 Production/Stable',
                   'Intended Audience :: Science/Research',
                   'Topic :: Scientific/Engineering :: Astronomy',],
      packages=find_packages(),
      package_data={'pylinear':['config/defaults.yml','synthphot/filters/*filt']})



#from setuptools import setup,find_packages
#import pylinear.__init__ as info
#
#setup(name='pylinear',\
#      version=info.__version__,\
#      author=info.__author__,\
#      author_email=info.__email__,\
#      keywords='grism linear python',\
#      description=info.__description__,\
#      license=info.__license__,\
#      entry_points={'console_scripts':['pylinear=pylinear.linear:main']},
#      install_requires=['numpy','scipy','ruamel.yaml','emcee','shapely',\
#                        'polyclip','h5axeconfig','argparse','astropy'],\
#      classifiers=['Development Status :: 4 Beta',\
#                   'Intended Audience :: Science/Research',
#                   'Topic :: Scientific/Engineering :: Astronomy',],\
#      packages=find_packages(),\
#      package_data={'pylinear':['config/defaults.yml','synthphot/filters/*filt']})
