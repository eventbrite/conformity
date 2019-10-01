Conformity - Declarative Schema for Python
==========================================

Release: |version|

.. image:: https://pepy.tech/badge/conformity
    :target: https://pepy.tech/project/conformity

.. image:: https://img.shields.io/pypi/l/conformity.svg
    :target: https://pypi.python.org/pypi/conformity

.. image:: https://api.travis-ci.org/eventbrite/conformity.svg
    :target: https://travis-ci.org/eventbrite/conformity

.. image:: https://img.shields.io/pypi/v/conformity.svg
    :target: https://pypi.python.org/pypi/conformity

.. image:: https://img.shields.io/pypi/wheel/conformity.svg
    :target: https://pypi.python.org/pypi/conformity

.. image:: https://img.shields.io/pypi/pyversions/conformity.svg
    :target: https://pypi.python.org/pypi/conformity

**Conformity** is a declarative schema validation library designed for use in libraries, services, application
settings, and more.

------------

**In just a few lines of code, you can define and validate a schema:**

.. code-block:: python

    >>> person_schema = fields.Dictionary(
            {
                'name': fields.UnicodeString(),
                'height': fields.Float(gt=0),
                'age': fields.Nullable(fields.Integer(gte=0)),
                'eye_color': fields.Constant('blue', 'brown', 'black', 'green', 'yellow', 'hazel'),
            },
            optional_keys=('eye_color', ),
        )
    >>> person_schema.errors({})
    [Error(message='Missing key: name', code='MISSING', pointer='name'),
     Error(message='Missing key: height', code='MISSING', pointer='height'),
     Error(message='Missing key: age', code='MISSING', pointer='age')]
    >>> person_schema.errors({'name': 'Scott', 'height': -2.0, 'age': 25})
    [Error(message='Value not > 0', code='INVALID', pointer='height')]
    >>> person_schema.errors({'name': 'Scott', 'height': 1.9, 'age': 25, 'eye_color': 'purple'})
    [Error(message='Value is not one of: "black", "blue", "brown", "green", "hazel", "yellow"', code='UNKNOWN', pointer='eye_color')]
    >>> person_schema.errors({'name': 'Scott', 'height': 1.9, 'age': 25, 'eye_color': 'brown'})
    []
    >>> @validator.validate_call(fields.Dictionary({'person': person_schema}), returns=fields.Boolean())
        def insert_person(person):
            return True
    >>> insert_person(person={})
    ValidationError: Invalid keyword arguments:
      - person.name: Missing key: name
      - person.height: Missing key: height
      - person.age: Missing key: age
    >>> insert_person(person={'name': 'Scott', 'height': 1.9, 'age': 25, 'eye_color': 'purple'})
    ValidationError: Invalid keyword arguments:
      - person.eye_color: Value is not one of: "black", "blue", "brown", "green", "hazel", "yellow"
    >>> insert_person(person={'name': 'Scott', 'height': 1.9, 'age': 25, 'eye_color': 'brown'})
    True


Table of Contents
-----------------

.. toctree::
   :maxdepth: 2

   fields
   settings
   validators
   reference
   sphinx
   contributing
   history


Indices, Tables, and Searching
------------------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
