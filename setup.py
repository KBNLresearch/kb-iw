#!/usr/bin/env python
"""Setup script for kb-iw"""
import codecs
import os
import re
from setuptools import setup, find_packages

def read(*parts):
    """Read file and return contents"""
    path = os.path.join(os.path.dirname(__file__), *parts)
    with codecs.open(path, encoding='utf-8') as fobj:
        return fobj.read()

INSTALL_REQUIRES = ['setuptools',
                    'lxml',
                    'pyvips',
                    'jpylyzer',
                    'pyexiftool']
PYTHON_REQUIRES = '>=3.9'

README = open('README.md', 'r')
README_TEXT = README.read()
README.close()

setup(name='kb-iw',
      packages=find_packages(),
      version='0.1.0',
      license='Apache License (https://www.apache.org/licenses/LICENSE-2.0)',
      install_requires=INSTALL_REQUIRES,
      python_requires=PYTHON_REQUIRES,
      platforms=['POSIX', 'Windows'],
      description='KB Image Workflow Tool',
      long_description=README_TEXT,
      long_description_content_type='text/markdown',
      author='Johan van der Knijff',
      author_email='johan.vanderknijff@kb.nl',
      maintainer='Johan van der Knijff',
      maintainer_email='johan.vanderknijff@kb.nl',
      url='https://github.com/KBNLresearch/kb-iw',
      package_data={'kbiw': ['*.*',
                                'conf/*.*',
                                'schemas/*.*']},
      entry_points={'console_scripts': [
          'kb-iw = kbiw.kbiw:main',
      ]},
      classifiers=[
          'Environment :: Console',
          'Programming Language :: Python :: 3',
      ]
     )
