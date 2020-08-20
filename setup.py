import sys

from setuptools import (
    find_packages,
    setup,
)

from conformity import __version__


def readme():
    with open('README.rst') as f:
        return f.read()


country_requires = [
    'pycountry<19.7.15;python_version<"3"',
    'pycountry>=19.7.15;python_version>="3"',
]

spinx_requires = [
    'sphinx~=2.2;python_version>="3.6"',
]

tests_require = [
    'freezegun',
    'mock;python_version<"3.3"',
    'mypy~=0.740;python_version>"3.4"',
    'pytest',
    'pytest-cov',
    'pytest-runner',
    'pytz',
] + country_requires + spinx_requires

setup(
    name='conformity',
    version=__version__,
    author='Eventbrite, Inc.',
    author_email='opensource@eventbrite.com',
    description='Cacheable schema description and validation',
    long_description=readme(),
    url='http://github.com/eventbrite/conformity',
    packages=list(map(str, find_packages(include=['conformity', 'conformity.*']))),
    package_data={
        str('conformity'): [str('py.typed')],  # PEP 561,
        str('conformity.sphinx_ext'): [str('static/*')],
    },
    zip_safe=False,  # PEP 561
    include_package_data=True,
    install_requires=[
        'typing~=3.7.4;python_version<"3.5"',
    ],
    tests_require=tests_require,
    setup_requires=['pytest-runner'] if {'pytest', 'test', 'ptr'}.intersection(sys.argv) else [],
    test_suite='tests',
    extras_require={
        'country': country_requires,
        'sphinx': spinx_requires,
        'docs': spinx_requires + country_requires,
        'testing': tests_require,
    },
    license='Apache 2.0',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development',
    ],
    project_urls={
        'Documentation': 'https://conformity.readthedocs.io',
        'Issues': 'https://github.com/eventbrite/conformity/issues',
        'CI': 'https://travis-ci.org/eventbrite/conformity/',
    },
)
