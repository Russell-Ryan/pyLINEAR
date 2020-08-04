from setuptools import setup,find_packages
#import os


# check some things
#for key in ['PYLINEAR_CONFIG']:
#    if key not in os.environ:        
#        print("Unable to setup pyLINEAR: must set '{}'".format(key))
#        exit(1)





ld='The python implementation of the LINEAR algorithm as developed Ryan, Casertano, & Pirzkal 2018: https://ui.adsabs.harvard.edu/abs/2018PASP..130c4501R/abstract'

rryan='git+https://github.com/russell-ryan/'
#rryan='git+ssh://git@github.com/russell-ryan/'
       
reqs=['numpy>1.16','scipy','astropy','emcee','h5py','colorlog',
      'pysiaf','pkginfo','shapely','tqdm','psutil','matplotlib']

      #'h5axeconfig @ git+https://github.com/russell-ryan/h5axeconfig'.format(rryan),
      #'fitsimage @ {}fitsimage#egg=fitsimage'.format(rryan),





#https://docs.python.org/2/distutils/setupscript.html
setup(name='pylinear3',
      version='2.0',
      author='Russell Ryan',
      author_email='rryan@stsci.edu',
      keywords=['grism','linear','WFC3','HST','slitless spectroscopy'],
      description='Linear Reconstruction of Slitless Spectroscopy',
      long_description=ld,
      maintainer='Russell Ryan',
      license='MIT',
      url='https://github.com/Russell-Ryan/pyLINEAR',
      platforms='posix',
      install_requires=reqs,
      entry_points={'console_scripts':['pylinear3=pylinear3.cli.pylinear:main']}, 
      classifiers=['Development Status :: 5 Production/Stable',
                   'Intended Audience :: Science/Research',
                   'Topic :: Scientific/Engineering :: Astronomy',],
      packages=find_packages(),
      package_data={'pylinear3':['sedphot/filters/*filt',
                                 'grism/instruments/instruments.xml']})

                                 
#'grism/siaf/siaf.h5']})
                        

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
