from setuptools import setup, find_packages
from conformity import __version__

setup(
    name='conformity',
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'six',
    ],
    test_suite='conformity.tests',
)
