from __future__ import absolute_import
from setuptools import setup

setup(
    name='TCT Toolchain Tool',
    version='1.1.0',
    py_modules=['tct'],
    packages= ['tctlib'],
    include_package_data=True,
    install_requires=[
        'click',
        'pyyaml',
    ],
    entry_points='''
        [console_scripts]
        tct=tct:cli
    ''',
)
