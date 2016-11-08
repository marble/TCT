from setuptools import setup

setup(
    name='TCT Toolchain Tool',
    version='0.1.4',
    py_modules=['tct'],
    packages= ['tctlib'],
    include_package_data=True,
    install_requires=[
        'click', 'pyyaml'
    ],
    entry_points='''
        [console_scripts]
        tct=tct:cli
    ''',
)
