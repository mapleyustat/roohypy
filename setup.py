# !/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup # Always prefer setuptools over distutils
from codecs import open  # To use a consistent encoding
from os import path
import numpy as np

#from distutils.core import setup
#from distutils.extension import Extension
#from Cython.Build import cythonize

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
# with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
#    long_description = f.read()
    
# List all the packages
packages=["roohypy",
          "roohypy.core",
          "roohypy.models",
          "roohypy.simulators",
          "roohypy.tools",
          "roohypy.tools.generators",
          "roohypy.tools.hdf5",
          "roohypy.tools.analysis",
          "roohypy.tools.preprocess"]

setup(
    name='roohypy',
    version='1.0.1',
    description='Python package for simulating the dynamics of agent on temporal multiplex networks',
    long_description='',
    url='https://github.com/ranaivomahaleo/roohypy',
    author='Ranaivo Razakanirina',
    author_email='ranaivo.razakanirina@atety.com',
    license='BSD 3-clause',
    #nstall_requires=['networkx', 'numpy', 'bitshuffle', 'scipy', 'h5py'],
    
    #ext_modules = cythonize(["roohypy/models/c_gtmodel.pyx"],
    #                include_path=[np.get_include()]),
    #include_dirs=[np.get_include()],

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Scientific/Engineering :: Physics'],
    keywords=['Multiplex', 'Econophysics', 'discrete mathematics', 'discrete dynamical systems'],
    packages=packages
    
)