Changelog
=========

1.28.0 (2020-09-09)
-------------------
- [MINOR] Add deprecation support (#88)

1.27.3 (2020-06-29)
-------------------
- Add introspect type to IPAddress

1.27.2 (2020-03-06)
-------------------
- [PATCH] Add Python 3.8 bdist_wheel support

1.27.1 (2020-03-05)
-------------------
- [PATCH] Differentiate import errors from other validation errors (#86)

1.27.0 (2020-02-03)
-------------------
- [MINOR] Add currency code field (#85)

1.26.8 (2019-12-02)
-------------------
- [PATCH] Fix typing issues introduced with MyPy 0.750 (#84)

1.26.7 (2019-12-02)
-------------------
- [PATCH] Fix Constant field when receiving unhashable values (#83)

1.26.6 (2019-11-04)
-------------------
- [PATCH] ClassConformitySchema should support SchemalessDictionaries, too

1.26.5 (2019-11-01)
-------------------
- [PATCH] Add support for Python 3.8

1.26.4 (2019-11-01)
-------------------
- [PATCH] [SPHINX] Soft fail getting annotations when source not found

1.26.3 (2019-10-01)
-------------------
- [PATCH] Improve documentation
- [PATCH] Fix new MyPy errors and remove unnecessary comments
- [PATCH] Fix .readthedocs.yml

1.26.2 (2019-09-16)
-------------------
- [PATCH] Fix a Sphinx bug that breaks uses of :ref:, etc.
- [PATCH] Add project URLs to setup.py

1.26.1 (2019-09-15)
-------------------
- [PATCH] Fix bug in Sphix ext improperly resolving signatures

1.26.0 (2019-09-13)
-------------------
- [MINOR] Add Python logging configuration validation schema
- [MINOR] Fix #71: Refactor the fields supporting Currint amounts
- [MINOR] Getting documentation ready for Read the Docs
- [PATCH] Really fix find_packages
- [PATCH] Restore use of find_packages that should not have been removed
- [MINOR] Fix #68 and find and fix other issues with typing
- [MINOR] Implement #65: Add support for generic Settings objects
- [PATCH] Clean up Travis file using config.travis-ci.org

1.25.0 (2019-06-13)
-------------------
- [MINOR] Add PythonPath field, superclass of TypePath
- [PATCH] Add more tests to ensure class schema extension behavior

1.24.3 (2019-06-12)
-------------------
- [PATCH] Regression: Fix Dictionary subclass processing and validation

1.24.2 (2019-06-12)
-------------------
- [PATCH] Make validated functions and methods introspectable

1.24.1 (2019-06-11)
-------------------
- [PATCH] Add PEP-561 type marker file

1.24.0 (2019-06-07)
-------------------
- [PATCH] Do some cleanup post-typing-integration
- [MINOR] Add new ClassConfigurationSchema field

1.23.0 (2019-06-05)
-------------------
- [MINOR] Support eager argument validation and type hints

1.22.0 (2019-06-04)
-------------------
- [MINOR] Rewrite validate_call and validate_method to handle positional args
- [MINOR] Add minimum and maximum length to SchemalessDictionary
- [MINOR] Add TypeReference and TypeName fields

1.21.0 (2019-04-17)
-------------------
- [PATCH] Switch from inconsistent-quotes to consistent single-quotes
- [PATCH] Add iSort settings and apply to project

1.20.0 (2019-04-10)
-------------------
- [MINOR] Bump Attrs, drop Py3.4 support, add Tox+Docker for local tests
- [PATCH] Fix EmailAddress whitelist not working (#46)

1.19.2 (2019-01-30)
-------------------
- [PATCH] Fix bug with string length restrictions and introspection
- [PATCH] Minor fixes to CountryCodeField

1.19.1 (2019-01-29)
-------------------
- [PATCH] PyPi releases now require PyOpenSSL

1.19.0 (2019-01-29)
-------------------
- [MINOR] Enhance Dictionary field to permit ordered key documentation

1.18.0 (2019-01-04)
-------------------
- [MINOR] Added CountryCodeField to Conformity
- [MINOR] Add introspect_type attribute to all fields (#43)

1.17.2 (2018-11-15)
-------------------
- [PATCH] Permit a newer Attrs version and confirm it works

1.17.1 (2018-10-24)
-------------------
- [PATCH] Fixed a bug where booleans passed Integer validation

1.17.0 (2018-09-06)
-------------------
- [MINOR] Add support for set and frozenset types

1.16.0 (2018-08-29)
-------------------
- Added currency Amount and AmountDictionary field (#38)

1.15.1 (2018-06-13)
-------------------
- [PATCH] Field subclasses that use Attrs must use attr.s

1.15.0 (2018-06-07)
-------------------
- [MINOR] Add support for fields of type decimal.Decimal
- Include import in readme example

1.14.0 (2018-05-25)
-------------------
- [MINOR] Fix three bugs in the email field

1.13.0 (2018-05-12)
-------------------
- [MINOR] Add support for extending dictionaries to simplify similar schemas
- [PATCH] Simple fix to readme syntax

1.12.0 (2018-05-01)
-------------------
- [MINOR] Add support for machine-readable error codes

1.11.0 (2018-04-19)
-------------------
- [MINOR] Make temporal type support more flexible

1.10.0 (2018-04-10)
-------------------
- added email validator

1.9.1 (2018-02-16)
------------------
- [PATCH] Ensure optional_keys is a set, introspects to a list

1.9.0 (2018-02-13)
------------------
- Add flag to disallow empty strings
- Fix: Nullable introspection incorrectly squashed all inner introspection into a string
- Add support for specifying minimum required string length

1.8.0 (2018-02-06)
------------------
- Add support for nullable fields using Nullable

1.7.5 (2018-02-05)
------------------
- Use Travis job stages so that deploy doesn't happen unless all tests pass

1.7.4 (2018-02-05)
------------------
- Fix Travis deploy step

1.7.3 (2018-02-05)
------------------
- No functional changes at all
- Add license to setup, capitalize readme title
- Use Invoke Release for releases going forward

1.7.2 (2018-01-19)
------------------
- Add correct deploy info to Travis file
- Fix typo in README file

1.7.1 (2018-01-18)
------------------
- Add missing deploy info to Travis file

1.7.0 (2018-01-18)
------------------
- Upgrade attrs to ~=17.4
- Improve code style
- Add PyTest support

1.6.1 (2017-10-14)
------------------
- Downgrade attrs from >16 (17.x) to ~=16.3 to fix version conflict error

1.6.0 (2017-08-11)
------------------

- Constant now takes multiple possible options and accepts any of them
- Added a UnicodeDecimal type that validates decimals transported as unicode strings.


1.5.0 (2017-05-02)
------------------

- Added BooleanValidator field
- Fixed behaviour when subclassing Dictionary to provide attributes in class body


1.4.0 (2017-05-01)
------------------

- Added Latitude and Longitude fields
- Added IPv4Address, IPv6Address, and IPAddress fields
- Added Any and All combinatorial fields
- Dictionary can now be subclassed, `contents` and `optional_keys` may be provided in the class body.


1.3.1 (2017-04-25)
------------------

- Error class now uses attrs rather than custom reimplementation


1.3.0 (2017-04-13)
------------------

- Add validation and description funcionality to fields for introspection
- Now compatible with Python 3


1.2.0 (2017-02-06)
------------------

- errors() now returns Error instances instead of error message strings


1.1.1 (2016-11-03)
------------------

- Float inherits methods from Integer
- @validate_call / @validate_method decorators preserve meta by using funtools.wraps


1.1.0 (2016-10-25)
------------------

- new types: Temporal, Tuple, ObjectInstance, SchemalessDictionary
- renamed 'collections' to 'structures' to avoid name clash


1.0.0 (2016-10-04)
------------------

- Initial release
- validation marker
- @validate_method decorator
