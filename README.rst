Conformity
==========

.. image:: https://api.travis-ci.org/eventbrite/conformity.svg
    :target: https://travis-ci.org/eventbrite/conformity

.. image:: https://img.shields.io/pypi/v/conformity.svg
    :target: https://pypi.python.org/pypi/conformity

.. image:: https://img.shields.io/pypi/l/conformity.svg
    :target: https://pypi.python.org/pypi/conformity


A low-level, declarative schema validation library.

Declare a schema:

.. code:: python

    from conformity.fields import Dictionary, Float, Integer, List, UnicodeString

    person = Dictionary({
        "name": UnicodeString(),
        "height": Float(gte=0),
        "event_ids": List(Integer(gt=0)),
    })

Check to see if data is valid:

.. code:: python

    data = {"name": "Andrew", "height": 180.3, "event_ids": [1, "3"]}
    errors = person.errors(data)

    # Key event_ids: Index 1: Not an integer

And wrap functions to validate on the way in and out:

.. code:: python

    kwargs = Dictionary({
        "name": UnicodeString(),
        "score": Integer(),
    }, optional_keys=["score"])

    @validate_call(kwargs, UnicodeString())
    def greet(name, score=0):
        if score > 10:
            return "So nice to meet you, {}!".format(name)
        else:
            return "Hello, {}.".format(name)

There's support for basic string, numeric, geographic, temporal, networking, and other field types, with everything
easily extensible (optionally via subclassing).


Errors are always instances of ``conformity.error:Error``, and each error has a ``message``, a ``code``, and a
``pointer``:

- ``message`` is a plain-language (English) explanation of the problem.
- ``code`` is a machine-readable code that, in most cases, is ``INVALID`` (using the constant
  ``conformity.error:ERROR_CODE_INVALID``). In ``Dictionary``, the error code is ``MISSING`` (``ERROR_CODE_MISSING``)
  for required keys that aren't present and ``UNKNOWN`` for extra keys that aren't allowed. In ``Constant``, the error
  code is ``UNKNOWN`` for values that don't match the allowed value or values. In ``Polymorph``, the error code is
  ``UNKNOWN`` for unknown switch values when no ``__default__`` is present.
- ``pointer`` is ``None`` for errors in most field types. However, for data structure field types (``List``,
  ``Dictionary``, ``SchemalessDictionary``, ``Tuple``), ``pointer`` is a string representing the dotted path to the
  offending value in the structure.


Interface
---------

Anything can be a Conformity validator as long as it follows this interface:

* An ``errors(value)`` method that returns a list of ``conformity.error:Error`` objects for each error or an empty
  list or ``None`` if the value is clean.

* An ``introspect()`` method, that returns a dictionary describing the field. The format of this dictionary has to vary
  by field, but it should reflect the names of keyword arguments passed into the constructor, and provide enough
  information to entirely re-create the field as-is. Any sub-fields declared for structures should be represented using
  their own ``introspect()`` output. The dictionary must also contain a ``type`` key that contains the name of the
  type, but this should use lower case and underscores rather than the class name. It can also contain a ``description``
  key which should be interpreted as the human-readable reason for the field.
