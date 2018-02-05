Conformity
==========

.. image:: https://api.travis-ci.org/eventbrite/conformity.svg
    :target: https://travis-ci.org/eventbrite/conformity

.. image:: https://img.shields.io/pypi/v/conformity.svg
    :target: https://pypi.python.org/pypi/conformity

.. image:: https://img.shields.io/pypi/l/conformity.svg
    :target: https://pypi.python.org/pypi/conformity


A low-level, declarative schema validation library.

Declare a schema::

    person = Dictionary({
        "name": UnicodeString(),
        "height": Float(gte=0),
        "event_ids": List(Integer(gt=0)),
    })

Check to see if data is valid::

    data = {"name": "Andrew", "height": 180.3, "event_ids": [1, "3"]}
    person.errors(data)

    # Key event_ids: Index 1: Not an integer

And wrap functions to validate on the way in and out::

    kwargs = Dictionary({
        "name": UnicodeString(),
        "score": Integer(),
    }, optional_keys=["score"])

    @validate_call(kwargs, UnicodeString())
    def greet(name, score=0):
        if score > 10:
            return "So nice to meet you, %s!" % name
        else:
            return "Hello, %s." % name

There's support for basic string, numeric, geographic, temporal, networking,
and other field types, with everything easily extensible (optionally via
subclassing)


Interface
---------

Anything can be a Conformity validator as long as it follows this interface:

* An ``errors(value)`` method, that returns a list of ``confirmity.Error``
  objects for each error or an empty list if the value is clean.

* An ``introspect()`` method, that returns a dictionary describing the field.
  The format of this dictionary has to vary by field, but it should reflect the
  names of keyword arguments passed into the constructor, and provide enough
  information to entirely re-create the field as-is. Any sub-fields declared
  for structures should be represented using their own ``introspect()`` output.
  The dictionary must also contain a ``type`` key that contains the name of the
  type, but this should use lower case and underscores rather than the class
  name. It can also contain a ``description`` key which should be interpreted
  as the human-readable reason for the field.
