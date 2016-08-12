from setuptools import setup

setup(
    name='TCT Toolchain Tool',
    version='0.1',
    py_modules=['tct'],
    include_package_data=True,
    install_requires=[
        'click', 'pyyaml'
    ],
    entry_points='''
        [console_scripts]
        tct=tct:cli
    ''',
)
