from setuptools import setup,find_packages
import pylinear.__init__ as info

setup(name='pylinear',\
      version=info.__version__,\
      author=info.__author__,\
      author_email=info.__email__,\
      keywords='grism linear python',\
      description=info.__description__,\
      license=info.__license__,\
      entry_points={'console_scripts':['pylinear=pylinear.linear:main']},
      install_requires=['numpy','scipy','ruamel.yaml','emcee','shapely',\
                        'polyclip','h5axeconfig','argparse','astropy'],\
      classifiers=['Development Status :: 4 Beta',\
                   'Intended Audience :: Science/Research',
                   'Topic :: Scientific/Engineering :: Astronomy',],\
      packages=find_packages(),\
      package_data={'pylinear':['config/defaults.yml','synthphot/filters/*filt']})
