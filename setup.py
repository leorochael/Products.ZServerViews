##############################################################################
#
# Copyright (c) 2013 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from setuptools import setup
from setuptools import find_packages
import os.path

version = open(os.path.join("Products","ZServerViews",
                            "version.txt")).read().strip()
description = """
Provide infrastructure for plugging views that run directly at the ZServer
thread
""".strip()

setup(name='Products.ZServerViews',
      version=version,
      description=description,
      long_description=open("README.rst").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Zope2",
        "Intended Audience :: System Administrators",
        ],
      keywords='zope2 plone',
      author='Leonardo Rochael Almeida',
      author_email='leorochael@gmail.com',
      url='http://pypi.python.org/pypi/Products.ZServerViews',
      license='ZPL',
      packages=find_packages(),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'Zope2',
      ],
      extras_require = {
          'test': [
                  'unittest2',
                  'plone.testing [z2]',
                  'IPython'
              ]
      },
)
