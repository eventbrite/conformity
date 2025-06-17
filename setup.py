from __future__ import (
    absolute_import,
    unicode_literals,
)

import sys

from setuptools import (  # type: ignore
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

country_requires = [
    'pycountry<19.7.15;python_version<"3"',
    'pycountry>=19.7.15;python_version>="3"',
]

spinx_requires = [
    'sphinx~=3.5;python_version>="3.6" and python_version<"3.12"',
    'sphinx~=7.2;python_version>="3.12"',
    'jinja2==3.0.3;python_version>="3.6" and python_version<"3.12"',
    'jinja2>=3.1.2;python_version>="3.12"',
]

tests_require = [
    'freezegun==1.0.0',
    'mock;python_version<"3.3"',
    'mypy~=0.740;python_version>"3.4" and python_version<"3.12"',
    'mypy>=1.5.1;python_version>="3.12"',
    'pytest>4.2,<5.4;python_version<"3.12"',
    'pytest>=7.4.0;python_version>="3.12"',
    'pytest-cov~=2.5;python_version<"3.12"',
    'pytest-cov>=4.1.0;python_version>="3.12"',
    'coverage~=5.2;python_version<"3.12"',
    'coverage>=7.2.7;python_version>="3.12"',
    'pytest-runner',
    'pytz',
    'importlib-metadata~=5.0;python_version>"3.6" and python_version<"3.12"',
    'importlib-metadata>=6.8.0;python_version>="3.12"'
] + currency_requires + country_requires + spinx_requires

mypy_requires = [
    'types-six;python_version>="3.7"',
    'types-pytz;python_version>="3.7"',
]

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
    'attrs>=17.4,<24',
    'six',
    'typing~=3.7.4;python_version<"3.5"',
    ],
    tests_require=tests_require,
    setup_requires=['pytest-runner'] if {'pytest', 'test', 'ptr'}.intersection(sys.argv) else [],
    test_suite='tests',
    extras_require={
        'currency': currency_requires,
        'country': country_requires,
        'sphinx': spinx_requires,
        'docs': spinx_requires + country_requires + currency_requires,
        'testing': tests_require,
        'mypy': mypy_requires,
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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development',
    ],
    project_urls={
        'Documentation': 'https://conformity.readthedocs.io',
        'Issues': 'https://github.com/eventbrite/conformity/issues',
        'CI': 'https://travis-ci.org/eventbrite/conformity/',
    },
)
