from setuptools import setup, find_packages
from conformity import __version__

setup(
    name='conformity',
    version=__version__,
    author='Eventbrite, Inc.',
    description='Cacheable schema description and validation',
    long_description=(
        'Conformity allows easy creation of schemas to be checked against '
        'function calls, service calls, or other uses, designed in a manner '
        'that allows heavy caching and is entirely deterministic.'
        '\n\nFor more, see http://github.com/eventbrite/conformity/'
    ),
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'six',
        'attrs>=16',
    ],
    test_suite='conformity.tests',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development',
    ],
)
