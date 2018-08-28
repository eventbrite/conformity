from __future__ import absolute_import, unicode_literals

from setuptools import (
    find_packages,
    setup,
)

from conformity import __version__


def readme():
    with open('README.rst') as f:
        return f.read()


currency_requires = [
    'currint',
]

tests_require = [
    'pytest',
    'pytest-cov',
    'freezegun',
    'pytz',
] + currency_requires

setup(
    name='conformity',
    version=__version__,
    author='Eventbrite, Inc.',
    author_email='opensource@eventbrite.com',
    description='Cacheable schema description and validation',
    long_description=readme(),
    url='http://github.com/eventbrite/conformity',
    packages=list(map(str, find_packages(exclude=['*.tests', '*.tests.*', 'tests.*', 'tests']))),
    include_package_data=True,
    install_requires=[
        'six',
        'attrs~=17.4',
    ],
    tests_require=tests_require,
    setup_requires=['pytest-runner'],
    test_suite='tests',
    extras_require={
        'currency': currency_requires,
        'testing': tests_require,
    },
    license='Apache 2.0',
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
