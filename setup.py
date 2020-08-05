from setuptools import setup,find_packages




ld='The python implementation of the LINEAR algorithm as developed Ryan, Casertano, & Pirzkal 2018: https://ui.adsabs.harvard.edu/abs/2018PASP..130c4501R/abstract'

rryan='git+https://github.com/russell-ryan/'
#rryan='git+ssh://git@github.com/russell-ryan/'
       
reqs=['numpy>1.16','scipy','astropy','emcee','h5py',
      'pysiaf','pkginfo','shapely','tqdm','psutil','matplotlib',
      'fitsimage @ {}fitsimage'.format(rryan),
      'colorlog @ {}colorlog'.format(rryan),
      'polyclip @ {}polyclip'.format(rryan)]
      



#https://docs.python.org/2/distutils/setupscript.html
setup(name='pylinear',
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
      entry_points={'console_scripts':['pylinear=pylinear.cli.pylinear:main']}, 
      classifiers=['Development Status :: 5 Production/Stable',
                   'Intended Audience :: Science/Research',
                   'Topic :: Scientific/Engineering :: Astronomy',],
      packages=find_packages(),
      package_data={'pylinear':['sedphot/filters/*filt',
                                'grism/instruments/instruments.xml']})

              
