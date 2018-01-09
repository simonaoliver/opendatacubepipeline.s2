#!/usr/bin/env python

from setuptools import setup

setup(name='s2pkg',
      version='0.0.1',
      description=('A temporary solution to get packaging underway. '
                   'Code will eventually be ported eo-datasets.'),
      packages=['s2pkg'],
      install_requires=[
          'click',
          'folium',
          'geopandas',
          'h5py',
          'luigi',
          'numpy',
          'pyyaml',
          'rasterio',
          'scikit-image',
          'shapely',
          'structlog',
          'eodatasets'
      ],
      dependency_links=[
          'git+http://github.com/GeoscienceAustralia/eo-datasets@develop#egg=eodatasets-0.1dev'
      ],
      scripts=['bin/s2package', 'bin/ard_pbs', 'bin/search_s2'],
      include_package_data=True)
