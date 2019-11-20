from setuptools import setup,find_packages
import os

ld='The python implementation of the LINEAR algorithm as developed Ryan, Casertano, & Pirzkal 2018: https://ui.adsabs.harvard.edu/abs/2018PASP..130c4501R/abstract'



#https://docs.python.org/2/distutils/setupscript.html
setup(name='pylinear',
      version='1.0',
      author='Russell Ryan',
      author_email='rryan@stsci.edu',
      keywords='grism linear WFC3 HST',
      description='Linear Reconstruction of Slitless Spectroscopy',
      long_description=ld,
      maintainer='Russell Ryan',
      license='MIT',
      url='https://github.com/Russell-Ryan/pyLINEAR',
      platforms='posix',
      install_requires=['numpy>1.16','scipy','astropy','h5axeconfig @ git+https://github.com/russell-ryan/h5axeconfig#egg=h5axeconfig','fitsimage @ git+https://github.com/russell-ryan/fitsimage#egg=fitsimage','emcee','ruamel.yaml','pkginfo','shapely','tqdm','psutil','matplotlib'],
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
