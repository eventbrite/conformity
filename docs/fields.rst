Using Conformity Fields
=======================

The core of Conformity's schema validation lies within its extensive set of fields, detailed here. Most fields can
be imported either from their specific package (detailed below) or from ``conformity.fields``, but fields that require
extra dependencies (such as `PyCountry`_ or `Currint`_) and fields and constants from ``conformity.fields.logging``
must be imported directly from their specific package.

.. contents:: Contents
   :depth: 3
   :local:
   :backlinks: none


Basic Fields
------------

All Conformity fields inherit from `basic.Base <reference.html#conformity.fields.basic.Base>`_ (and, should you need
`create your own`_, they must inherit from ``Base``, too). It defines two key, abstract methods, ``errors`` and
``introspect``, which all Conformity fields must implement. ``errors`` returns an empty list if no errors were
encountered, or a list of one or more `error.Error <reference.html#conformity.error.Error>`_ objects if validation
failed.

An ``Error`` has three properties:

- ``code``: A machine-readable code identifying the nature of the error (required)
- ``message``: A human-readable message detailing the nature of the error (required)
- ``pointer``: A pointer to the location of the error, which has a value when the error occurred in a list, dictionary
  or other structure (optional)

``introspect`` is used to generate a dictionary containing introspection information that can be used to document
the schema or auto-generate type conversions. `PySOA`_ and the `Conformity Sphinx extensions <sphinx.html>`_ use
introspection to document fields and schemas in Conformity, PySOA, and other projects.

In addition to other constructor arguments that each field might have, all fields have an optional ``description``
keyword argument. You are encouraged to always provide this argument, as it powers self-documentation of your schemas
and settings.

There are several basic field types that encompass the validation of common primitives:

- `basic.Anything <reference.html#conformity.fields.basic.Anything>`_: The simplest concrete type, its values can be
  literally anything. Its ``errors`` method always returns an empty list.
- `basic.Constant <reference.html#conformity.fields.basic.Constant>`_: This can be used to require that a value be
  a specific, constant value or one of a set of allowed values. Some examples:

  .. code-block:: python

      fields.Constant('MUST_BE_THIS')
      fields.Constant('option1', 'option2', 'option3', 'option4')
      fields.Constant(**set_of_values)

  It is not required that the values be strings. They can be numbers, integers, complex objects, or anything else you
  desire. Think of ``Constant`` as much like an enum.

- `basic.Hashable <reference.html#conformity.fields.basic.Hashable>`_: This ensures that the value can be hashed. Any
  type or content is valid, as long as calling ``hash(...)`` on the object succeeds without error.
- `basic.Boolean <reference.html#conformity.fields.basic.Boolean>`_: This ensures that the value is a ``bool``, either
  ``True`` or ``False``. Non-Boolean truth-y or false-y values are not permitted.
- `basic.Integer <reference.html#conformity.fields.basic.Integer>`_: This ensures that the value is an integer (floats
  are not permitted). It defines optional arguments ``gt``, ``gte``, ``lt``, and ``lte``, permitting you to establish
  boundaries for the values it validates. The values for these boundaries can be integers, floats, or instances of
  ``decimal.Decimal``.
- `basic.Float <reference.html#conformity.fields.basic.Float>`_: This ensures that the value is a float, and defines
  the same boundary arguments defined by ``Integer``.
- `basic.Decimal <reference.html#conformity.fields.basic.Decimal>`_: This ensures that the value is an instance of
  ``decimal.Decimal`` and defines the same boundary arguments defined by ``Integer``.
- `basic.UnicodeString <reference.html#conformity.fields.basic.UnicodeString>`_: This ensures that the value is a
  unicode string (``str`` in Python 3 and ``unicode`` in Python 2). It defines optional arguments ``min_length`` and
  ``max_length`` to establish boundaries for the value length and ``allow_blank`` (default ``True``) for whether
  blank values are allowed (if ``min_length`` is specified greater than zero, ``allow_blank`` is ignored).
- `basic.ByteString <reference.html#conformity.fields.basic.ByteString>`_: This ensures that the value is a byte string
  (``bytes`` in Python 3 and ``str`` in Python 2) and defines the same arguments as ``UnicodeString``.
- `basic.UnicodeDecimal <reference.html#conformity.fields.basic.UnicodeDecimal>`_: This ensures that the value is a
  unicode string that is also a valid argument for creating a ``decimal.Decimal`` (it matches decimal syntax).
- `meta.Null <reference.html#conformity.fields.meta.Null>`_: This indicates that the value must be null (``None``).
- `meta.Nullable <reference.html#conformity.fields.meta.Nullable>`_: You can wrap this value around any field to make
  it nullable. By default, all Conformity fields require the value to be non-null, but when wrapped with ``Nullable``,
  it becomes valid for their values to be ``None``:

  .. code-block:: python

      non_nullable_field = fields.UnicodeString()
      nullable_field = fields.Nullable(fields.UnicodeString())

  In this example, ``'hello'`` would be a valid value for ``non_nullable_field``, but ``None`` would not. However, both
  would be valid values for ``nullable_field``.


Geography, Dates & Times, and Networking
----------------------------------------

There are several common but less-primitive types that you might need to validate, and Conformity provides fields for
many of them (and you can always `create your own`_ and, if you want, submit it in a
`pull request <https://github.com/eventbrite/conformity>`_).

- `geo.Latitude <reference.html#conformity.fields.geo.Latitude>`_: A special extension of ``Float`` sets ``gte`` to
  ``-90`` if it is not set and forces it to be greater than ``-90`` if it is set and sets ``lte`` to ``90`` if it is
  not set and forces it to be less than ``90`` if it is set.
- `geo.Longitude <reference.html#conformity.fields.geo.Longitude>`_: A special extension of ``Float`` sets ``gte`` to
  ``-180`` if it is not set and forces it to be greater than ``-180`` if it is set and sets ``lte`` to ``180`` if it is
  not set and forces it to be less than ``180`` if it is set.
- `net.IPv4Address <reference.html#conformity.fields.net.IPv4Address>`_: An extension of ``UnicodeString`` that ensures
  that the string is a valid IPv4 address.
- `net.IPv6Address <reference.html#conformity.fields.net.IPv6Address>`_: An extension of ``UnicodeString`` that ensures
  that the string is a valid IPv6 address.
- `net.IPAddress <reference.html#conformity.fields.net.IPAddress>`_: An field that ensures that the unicode string is
  either a valid IPv4 address or a valid IPv6 address.
- `email.EmailAddress <reference.html#conformity.fields.email.EmailAddress>`_: An extension of ``UnicodeString`` that
  ensures that the string is a valid RFC 2822 email address. This validation is very thorough and supports all special
  characters, dot-atoms, and quoted-string unicode characters that are permitted. It supports an additional, optional
  ``whitelist`` argument that should be an iterable of domains and defaults to ``{'localhost'}``. If the email domain
  is present in this set, the domain portion of the email will be assumed correct and not validated.
- `temporal.DateTime <reference.html#conformity.fields.temporal.DateTime>`_: Ensures that the supplied type is an
  instance of ``datetime.datetime``. It has optional ``gt``, ``gte``, ``lt``, and ``lte`` arguments that, like
  ``Integer``, can set boundaries for the date-time object. These arguments, if specified, must be
  ``datetime.datetime`` objects.
- `temporal.Date <reference.html#conformity.fields.temporal.Date>`_: Ensures that the supplied type is an instance of
  ``datetime.date``. Its ``gt``, ``gte``, ``lt``, and ``lte`` arguments, if specified, must be ``datetime.date``
  objects.
- `temporal.Time <reference.html#conformity.fields.temporal.Time>`_: Ensures that the supplied type is an instance of
  ``datetime.time``. Its ``gt``, ``gte``, ``lt``, and ``lte`` arguments, if specified, must be ``datetime.time``
  objects.
- `temporal.TimeDelta <reference.html#conformity.fields.temporal.TimeDelta>`_: Ensures that the supplied type is an
  instance of ``datetime.timedelta``. Its ``gt``, ``gte``, ``lt``, and ``lte`` arguments, if specified, must be
  ``datetime.timedelta`` objects.
- `temporal.TZInfo <reference.html#conformity.fields.temporal.TZInfo>`_: Ensures that the supplied type is an instance
  of ``datetime.tzinfo``.

  .. note::
      The ``TZInfo`` field does not require `PyTz <https://pythonhosted.org/pytz/>`_ to work, but PyTz is certainly
      the easiest and only practicable way to create a ``datetime.tzinfo`` object which can be passed to
      ``TZInfo.errors``.


Structures: Lists, Dictionaries, and More
-----------------------------------------

So far we have examined relatively simple types, but the power in Conformity comes from its ability to have structures
of nested fields and perform nested validation on all of them. The fields in ``conformity.fields.structures`` establish
these structures.


Lists and Sets
++++++++++++++

`structures.List <reference.html#conformity.fields.structures.List>`_ and
`structures.Set <reference.html#conformity.fields.structures.Set>`_ provide the ability to have arbitrary-length
lists and sets (respectively) where each value matches some other Conformity schema. ``List`` supports objects of
type ``list`` and ``Set`` supports objects of type ``set`` and ``frozenset``. The both have optional ``min_length``
and ``max_length`` arguments that define boundaries for the collection size, but the key is the mandatory ``contents``
argument that defines the nested schema:

.. code-block:: python

    fields.List(fields.UnicodeString(allow_blank=False), min_length=3, max_length=20, description='Foo')
    fields.Set(fields.Integer(gte=0, lte=100), description='Bar')
    fields.Set(fields.Constant(**allowed_types), min_length=1, max_length=10)

When each of these fields is validated with an ``errors`` call, its own boundaries will be checked and also ``errors``
will be called on its ``contents`` for each value in the collection.


Dictionaries
++++++++++++

Dictionaries are the next logical structure to validate. Conformity provides
`structures.Dictionary <reference.html#conformity.fields.structures.Dictionary>`_ and
`structures.SchemalessDictionary <reference.html#conformity.fields.structures.SchemalessDictionary>`_ to support this
need.

``Dictionary`` has a ``contents`` argument that must be a ``typing.Mapping[typing.Hashable, fields.Base]``, which
defines the dictionary keys and their respective, nested Conformity value schemas. It also provides ``optional_keys``
(default empty) for when you want to make some dictionary keys optional and ``allow_extra_keys`` (default ``False``)
for when you want to permit any-value keys not defined by the ``contents``.

.. code-block:: python

    person_schema = fields.Dictionary(
        {
            'name': fields.UnicodeString(),
            'height': fields.Float(gt=0),
            'age': fields.Nullable(fields.Integer(gte=0)),
            'eye_color': fields.Constant('blue', 'brown', 'black', 'green', 'yellow', 'hazel'),
        },
        optional_keys=('eye_color', ),
        allow_extra_keys=True,
        description='Foo bar',
    )

One of the helpful features of ``Dictionary`` is its ``extend`` method, which allows you to create a new
``Dictionary`` which extends the original's schema without having to re-define everything:

.. code-block:: python

    extra_person_schema = person_schema.extend(
        contents={
            'employer': fields.UnicodeString(description='The ID code for the employer'),
            'country': fields.CountryCodeField(),
            'age': fields.Nullable(fields.Integer(gte=18)),
        },
        optional_keys=('employer', ),
        allow_extra_keys=False,
        replace_optional_keys=False,
        description='Extra foo bar',
    )

This ``extra_person_schema`` will have all the fields from ``person`` plus the new fields defined, and the minimum
age will have been overridden to 18. Because ``replace_optional_keys`` was ``False``, the ``optional_keys`` will now
be ``('eye_color', 'employer')``. Also, extra keys are now disallowed in this new field.

``Dictionary`` is useful for defining validation for a strict ``dict``, but sometimes you need something more flexible.
``SchemalessDictionary`` is for when you don't care about the exact key, you just care about the key and/or value
*types*. For example, perhaps it can be the request or response schema for a bulk submit or a bulk lookup:

.. code-block:: python

    response_schema = fields.SchemalessDictionary(
        key_type=fields.UnicodeString(description='The ID of the user requested in the input'),
        value_type=fields.Dictionary(
            {
                'id': fields.UnicodeString(description='The user ID'),
                'username': fields.UnicodeString(),
                'password': fields.ByteString(),
                'email': fields.EmailAddress(),
                'organization_id': fields.UnicodeString(description='The organization ID'),
            },
            optional_keys=('organization_id', )
            allow_extra_keys=True,
        ),
        min_length=0,
        max_length=100,
    )

As you can see above, ``SchemalessDictionary`` is quite flexible. It has ``key_type``, ``value_type``, ``min_length``,
and ``max_length`` fields, which are all optional. ``key_type`` and ``value_type`` can be any field that extends
``Base``.


Tuples
++++++

The `structures.Tuple <reference.html#conformity.fields.structures.Tuple>`_ field is a bit more niche than the other
four structure types. Unlike ``List`` and ``Set``, which both ensure that all of their values meet the same schema,
``Tuple`` is for defining a fixed-length collection where each value can be different. For example:

.. code-block:: python

    fields.Tuple(
        fields.UnicodeString(),
        fields.Integer(),
        fields.Boolean(),
        fields.Nullable(fields.UnicodeString()),
    )

In order to pass validation for this field, values most be ``tuple`` instances with exactly four items matching the
four schemas defined, in that order:

.. code-block:: python

    ('foo', 2, True)  # invalid
    (b'bar', 2, True, 'baz')  # invalid
    ('qux', 3, False, None)  # valid
    ('qux', 4, True, 'foo')  # valid

You can see a great example of ``Tuple`` in use in the positional-arguments example of
`Validating Function Calls <validators.html#validating-function-calls>`_.


Fields with Extra Dependencies
------------------------------

There are a handful of fields which you may find useful but which require extra dependencies to use.

`country.CountryCodeField <reference.html#conformity.fields.country.CountryCodeField>`_ is a special extension of
``Constant`` that ensures the value is a unicode string that is a valid ISO 3166 alpha-2 country code. It has one
argument, ``code_filter``, which if specified must be a ``typing.Callable[[typing.AnyStr], bool]``. The filter will be
passed a country code and should return ``True`` if that country code is allowed and ``False`` if it is not allowed.
This is an eager filter that will filter the allowed country codes when the instance is constructed instead of waiting
until validation time.

In order to use ``CountryCodeField``, you must specify the ``country`` extras dependency:

.. code-block:: bash

    # With pip
    pip install conformity[country]

.. code-block:: python

    # With setup.py
    install_requires=[
        ...
        'conformity[country]',
        ...
    ]

.. code-block:: text

    # With Pipfile
    conformity = {version="*", extras=["country"]}

There are four other fields that make use of `Currint`_ types if you specify the ``currint`` extras dependency:

- `currency.Amount <reference.html#conformity.fields.currency.Amount>`_: This field ensures that the value is an
  instance of ``currint.Amount``. It provides an optional ``valid_currencies`` argument which, by default, is the set
  of all ISO 4217 currency codes recognized by Currint. It also provides optional integer ``gt``, ``gte``, ``lt``, and
  ``lte`` boundary arguments that will be compared against the ``currint.Amount.value`` attribute.
- `currency.AmountRequestDictionary <reference.html#conformity.fields.currency.AmountRequestDictionary>`_: A special
  extension of ``Dictionary`` that enforces the standard JSON-compatible representation of a ``currint.Amount`` input
  value, which must have a string ``'currency'`` key and an integer ``'value'`` key:

  .. code-block:: json

      {
          "currency": "USD",
          "value": 1200,
      }

  This object, for example, represents USD 12.00. Like ``Amount``, it also has ``valid_currencies``, ``gt``, ``gte``,
  ``lt``, and ``lte`` optional arguments.
- `currency.AmountResponseDictionary <reference.html#conformity.fields.currency.AmountResponseDictionary>`_: A special
  extension of ``Dictionary`` that enforces the standard JSON-compatible representation of a ``currint.Amount``
  response value, which must have a string ``'currency'`` key and an integer ``'value'`` key and may optionally have
  string keys ``'major_value'`` and ``'display'``.

  .. code-block:: json

      {
          "currency": "USD",
          "value": 1200,
          "major_value": "12.00",
          "display": "12.00 USD",
      }
- `currency.AmountString <reference.html#conformity.fields.currency.AmountString>`_: A Unicode string field (which does
  not extend ``UnicodeString``) that enforces the value meets the currency format ``'CUR,1234'`` or ``'CUR:1234'``, and,
  like ``Amount``, supports ``valid_currencies``, ``gt``, ``gte``, ``lt``, and ``lte`` optional arguments.

- `currency.CurrencyCodeField <reference.html#conformity.fields.currency.CurrencyCodeField>`_: is a special extension of
``Constant`` that ensures the value is a Unicode string that enforces the value meets the currency format as ``'USD'``. It has one
argument, ``code_filter``, which if specified must be a ``typing.Callable[[typing.AnyStr], bool]``. The filter will be
passed a currency code and should return ``True`` if that currency code is allowed and ``False`` if it is not allowed.
This is an eager filter that will filter the allowed currency codes when the instance is constructed instead of waiting
until validation time.

Advanced Fields
---------------

There are several advanced fields that aren't used very often but that cater to complicated or niche requirements.
We'll cover them here, starting with the easiest.


Any and All
+++++++++++

`meta.Any <reference.html#conformity.fields.meta.Any>`_ and `meta.All <reference.html#conformity.fields.meta.All>`_ are
basically opposites. ``Any`` wraps two or more other Conformity fields (``Base``) and passes validation as long as
*at least one* of those fields passes validation. For example, if ``Any`` is used with three fields, and two fail to
vaidate but one passes, ``Any`` passes. Example:

.. code-block:: python

    number = fields.Any(fields.Integer(), fields.Float(), fields.Decimal(), fields.UnicodeDecimal())

With this definition, a value will be valid as long as it is an ``int``, ``float``, ``decimal.Decimal``, or unicode
string in valid decimal format. If it matches none of those, ``Any.errors`` will return a combined list of all of the
``Error`` objects collected from all four fields.

``All`` does the exact opposite, and passes validation only if *all* of the fields pass validation.

.. code-block:: python

    fields.All(
        fields.UnicodeString(),
        fields.BooleanValidator(...),
    )

In this case, the value must be a unicode string and also pass the custom validation specified in the
``BooleanValidator`` (more on that below).


Custom Validator Functions
++++++++++++++++++++++++++

It's possible that your validation rules can't be expressed in something as simple as a Conformity schema. You may
need more complex validation that requires context that can't be known within Conformity fields. Instead of
implementing a custom field, you can just use the
`meta.BooleanValidator <reference.html#conformity.fields.meta.BooleanValidator>`_ field. It takes several arguments:

- ``validator`` (required): A callable that takes a single argument (the value) and returns a ``bool`` indicating
  whether that value is valid or invalid
- ``validator_description`` (required): A unicode description string detailing what the validator function does
- ``error`` (required): The error message that should be set on ``Error.message`` when validation fails
- ``description`` (optional): The standard Conformity documentation string

.. code-block:: python

    fields.BooleanValidator(
        validator=custom_validator_function,
        validator_description='This custom validator does custom validation',
        error='This thing is custom-ly invalid',
    )


Objects, Types, and Python References
+++++++++++++++++++++++++++++++++++++

There are several fields that deal with objects, types, paths, and Python references in the ``conformity.fields.meta``
module.

- `meta.ObjectInstance <reference.html#conformity.fields.meta.ObjectInstance>`_: This validates that the value is an
  instance of the provided type or types. Its ``valid_type`` argument can be either a ``Type`` or a
  ``Tuple[Type, ...]``. During validation, ``errors`` calls ``isinstance``, passing the value as the first argument and
  ``self.valid_type`` as the second argument.
- `meta.TypeReference <reference.html#conformity.fields.meta.TypeReference>`_: This is similar to ``ObjectInstance``,
  but ensures that the value is a type instead of an instance. With no arguments, it simply ensures that
  ``isinstance(value, type)``. The optional ``base_classes`` argument can be either a ``Type`` or a
  ``Tuple[Type, ...]``, and if specified, ``errors`` checks ``issubclass(value, self.base_classes)``.
- `meta.PythonPath <reference.html#conformity.fields.meta.PythonPath>`_: This is a unicode string (though it does not
  extend ``UnicodeString``) that enforces that the value provided is an importable and referenceable Python path. A
  simple, top-level class, function, or attribute can use the format ``foo.bar.module.MyClass``,
  ``baz.qux.other_module.my_function``, etc. The more advanced form—with a colon separating the module and item—is
  optional for top-level items and required for non-top-level items, such as ``foo.bar.module:MyClass.InnerClass`` or
  ``baz.qux.other_module:OtherClass.my_method``. ``PythonPath`` attempts to import the module and resolve the Python
  object located at that path, and returns an error if it can't for any reason.

  ``PythonPath`` also has an optional argument ``value_schema``, which must be a Conformity field (``Base``). If
  specified, once the item has been successfully imported, ``errors`` will ensure that it passes validation in that
  ``value_schema``.

  .. code-block:: python

      fields.PythonPath(
          value_schema=fields.Dictionary({...}),
          description='A thing that does something',
      )

  .. note::

      ``PythonPath`` makes use of aggressive caching so that it's not frequently importing the same items over and
      over again. Even across multiple instances of ``PythonPath``, once ``foo.bar.module.MyClass`` (example) is
      imported and resolved, it will not have to be imported and resolved again, and will instead be obtained directly
      from cache.

- `meta.TypePath <reference.html#conformity.fields.meta.TypePath>`_: This extends ``PythonPath``. Instead of a
  ``value_schema`` argument, it provides an optional ``base_classes`` argument. It then sets its ``value_schema`` to a
  ``TypeReference`` of the same ``base_classes``. This is a way of requiring the imported Python path to be a type
  that optionally extends a specific base class.


Polymorphs
++++++++++

`meta.Polymorph <reference.html#conformity.fields.meta.Polymorph>`_ is an interesting and complicated field. It is
designed to switch which Conformity schema it uses to validate the input based on some value from the input. In the
simplest terms, the input is always a ``Mapping`` (dictionary, mutable or immutable). When creating a ``Polymorph``, you
provide it two mandatory fields:

- ``switch_field``: This is the name of a dictionary key that can always be found in the item being validated. The
  value associated with this key is used to determine which schema to use for validation.
- ``contents_map``: This is a mapping of possible values associated with the switch field key and the Conformity field
  that should be used to validate each one. Its allowed type is technically ``typing.Mapping[typing.Hashable, Base]``,
  but because the item validated has to be a mapping, the field used should, realistically, be either a ``Dictionary``
  or a ``SchemalessDictionary``. The special ``contents_map`` key ``__default__``, if present, will define a default
  schema for when the proper schema can't be determined based on the input. If not present, an error will be raised in
  this case.

.. code-block:: python

    fields.Polymorph(
        switch_field='type',
        contents_map={
            'dog': fields.Dictionary({'type': fields.UnicodeString(), ...}),
            'cat': fields.Dictionary({...}, allow_extra_keys=True),
            '__default__': fields.SchemalessDictionary(key_type=fields.UnicodeString()),
        },
        description='Be sure to write documentation for such a complicated field!',
    )

In this example, if the validated item's ``'type'`` field has a value of "dog," the first dictionary will be used to
validate the item. The value "cat" in ``'type'`` will result in the second dictionary's being used. Any other value
will result in the ``SchemalessDictionary`` being used, but would have resulted in an error without ``'__default__'``.
Note that the schema for each possible value must either be schemaless, have a ``'type'`` field that is a
``UnicodeString``, or have ``allow_extra_keys=True``, so that the ``'type'`` field used for switching in this case
passes validation.


Class Configuration Schemas
+++++++++++++++++++++++++++

`meta.ClassConfigurationSchema <reference.html#conformity.fields.meta.ClassConfigurationSchema>`_ is perhaps
Conformity's most advanced and powerful type. When used, the item validated must be a ``Mapping`` (dictionary, mutable
or immutable) with at least a key ``'path'``. This ``'path'`` will be validated using ``TypePath``, and the
``base_class`` argument to ``ClassConfigurationSchema`` will be passed to the ``TypePath``, if specified. The type
(class) resolved by each value of ``'path'`` must be decorated with ``@ClassConfigurationSchema.provider(...)``, which
specifies the (``Dictionary``) schema for that class's constructor's arguments (or an empty dictionary if there are
no arguments).

``ClassConfigurationSchema`` is best explained with examples. It starts with defining some kind of base class and then
one more more implementations:

.. code-block:: python

    class Widget(metaclass=abc.ABCMeta):
        @abc.abstractmethod
        def do(self):
            """Do widget stuff"""

    @fields.ClassConfigurationSchema.provider(fields.Dictionary({}))
    class BobbleWidget(Widget):
        def __init__(self):
            """No arguments"""

        def do(self):
            ... do things ...

    @fields.ClassConfigurationSchema.provider(fields.Dictionary(
        {
            'widget_name': fields.UnicodeString(),
            'do_count': fields.Integer(),
        },
        allow_extra_keys=True,
    ))
    class FumbleWidget(Widget):
        def __init__(self, widget_name: str, do_count: int, **kwargs):
            ... do things ...

        def do(self):
            ... do things ...

    @fields.ClassConfigurationSchema.provider(fields.Dictionary({'db': fields.ObjectInstance(DBConnection)}))
    class FidgetWidget(Widget):
        def __init__(self, db_connection: DBConnection):
            ... do things ...

        def do(self):
            ... do things ...


Once your classes are created, you define your schema:

.. code-block:: python

    config_schema = fields.ClassConfigurationSchema(
        base_class=Widget,  # this argument is optional and defaults to `object`
        default_path='com.foo.BobbleWidget',  # this argument is optional and only used if the item is missing 'path'
        description='You definitely need to document this.',  # optional, but encouraged
        eager_default_validation=False,  # this optional argument defaults to True
        add_class_object_to_dict=True,  # this optional argument defaults to True and controls a side effect (below)
    )

Now let's explore possible input values:

.. code-block:: python

    config1 = {'path': 'com.foo.BobbleWidget'}
    config2 = {
        'path': 'com.foo.FumbleWidget',
        'kwargs': {
            'widget_name': 'Hello',
            'do_count': 5,
        },
    }
    config3 = {
        'path': 'com.foo.FidgetWidget',
        'kwargs': {},
    }
    config4 = {}

In this case, ``config1`` would, when validated, resolve the ``BobbleWidget``. Since that class has an empty dictionary
as its schema, validation passes. ``config2`` would resolve to ``FumbleWidget``, and it would also pass validation
since it has a ``kwargs`` key whose contents pass the schema dictionary defined for that class. ``config3`` would fail
validation, because it is missing the ``db_connection`` required by the schema for ``FidgetWidget``. Finally,
``config4`` would pass, but only because ``default_path`` is set and ``BobbleWidget`` has no required arguments. If
``default_path`` were not set, or if ``BobbleWidget`` had required arguments, ``config4`` would fail validation.

``ClassConfigurationSchema`` is the only Conformity field whose validation process results in a side-effect on the item
validated. Once the type at ``'path'`` is imported and resolved, that type (not an instance of it) is added to the item
under the key ``'object'`` (this name was chosen for historical reasons related to `PySOA`_, and might be changed to
``'type'`` in Conformity 2). So, you can use the following code to resolve the path, validate the arguments, and
instantiate the type with those arguments:

.. code-block:: python

    if config_schema.errors(settings['widget_config']):
        raise ...

    widget = settings['widget_config']['object'](**settings['widget_config'].get('kwargs', {}))

If you do not desire the ``'object'`` side-effect, you can disable it by setting ``add_class_object_to_dict=False``. In
this case, you would need to do a bit more work to instantiate the widget:

.. code-block:: python

    if config_schema.errors(settings['widget_config']):
        raise ...

    widget_type = PythonPath.resolve_python_path(settings['widget_config']['path'])
    widget = widget_type(**settings['widget_config'].get('kwargs', {}))

The final argument of note is ``eager_default_validation``. It is ignored unless ``default_path`` is specified. If
``default_path`` is specified and ``eager_default_validation`` is ``True`` (the default), the class at ``default_path``
will be eagerly imported and resolved and checked to make sure it has a valid ``@ClassConfigurationSchema.provider``
decorator.


Logging Helpers
---------------

The `Python Logging dictionary configuration <https://docs.python.org/3/library/logging.config.html#configuration-dictionary-schema>`_
is a common dictionary-based settings/configuration object in need of validation. Python does some level of validation
on values passed to ``logging.config.dictConfig``, but that validation is not necessarily thorough, and the errors
arising from an invalid configuration are often cryptic and hard to track down.

The `conformity.fields.logging <reference.html#conformity.fields.logging.PythonLogLevel>`_ module contains one helper
field ``PythonLogLevel``, which is a simple ``Constant`` with log level names as the pre-defined values, and some
helper schemas to make it easier for you to accurately validate logging settings:

- ``PYTHON_ROOT_LOGGER_SCHEMA``: The schema (``Dictionary`` instance) for the root logger
- ``PYTHON_LOGGER_SCHEMA``: The schema (``Dictionary`` instance) for all other loggers
- ``PYTHON_LOGGING_CONFIG_SCHEMA``: The schema (``Dictionary`` instance) for the entire Python logging config
  dictionary format.


.. _create your own:

Creating Your Own Fields
------------------------

If none of these fields meet your needs, creating your own field is a matter of extending ``Base``, defining arguments,
and implementing ``errors`` and ``introspect``. We recommend `Dataclasses`_ (if you're using Python 3.7 or newer) or
`Attrs`_ to avoid boilerplate code in your field. Attrs is a bit more powerful because it includes validation features,
unlike Dataclasses. If you want to submit your field as a pull request to Conformity, we require you to use Attrs and
Python Type Annotation comments to avoid boilerplate code and to be compatible with Python 2.7 through 3.7.

.. code-block:: python

    class Widget(Base):

        minimum_something = attr.ib(validator=attr_is_instance(Something))  # type: Something
        description = attr.ib(
            default=None,
            validator=attr_is_optional(attr_is_string()),
        )  # type: typing.Optional[six.text_type]

        def errors(self, value):  # type: (typing.Any) -> typing.List[Error]
            errors = []

            ...

            return errors

        def introspect(self):
            return strip_none({
                'type': 'widget',
                'minimum_something': six.text_type(self.minimum_something),
                'description': self.description,
            })

``strip_none`` is a `handy utility <reference.html#conformity.utils.strip_none>`_ in ``conformity.utils`` for removing
dictionary items whose value is ``None``.  ``attr_is_instance``, ``attr_is_optional``, and ``attr_is_string`` are
validators provided by Attrs.


.. _PyCountry: https://github.com/flyingcircusio/pycountry
.. _Currint: https://github.com/eventbrite/currint
.. _PySOA: https://github.com/eventbrite/pysoa
.. _Attrs: https://www.attrs.org/en/stable/
.. _Dataclasses: https://docs.python.org/3/library/dataclasses.html
