Validating Values and Invocations
=================================

Conformity provides a collection of validator utilities to help you validate input against defined Conformity schemas.
Which validator you employ depends on whether you want to validate inline code or validate function and method calls.

.. contents:: Contents
   :depth: 3
   :local:
   :backlinks: none


Simple Validation
-----------------

When performing simple validation, you can use ``validate`` function or the field's ``errors`` method. Consider the
following schema:

.. code-block:: python

    person_schema = fields.Dictionary(
        {
            'name': fields.UnicodeString(),
            'height': fields.Float(gt=0),
            'age': fields.Nullable(fields.Integer(gte=0)),
            'eye_color': fields.Constant('blue', 'brown', 'black', 'green', 'yellow', 'hazel'),
        },
        optional_keys=('eye_color', ),
    )

In ``conformity.validator`` there is a `validate <reference.html#conformity.validator.validate>`_ function that can
validate any value against a schema and raise a ``ValidationError`` should validation fail:

.. code-block:: python

    >>> validate(person_schema, {'name': 'Scott', 'height': 1.9, 'age': 25, 'eye_color': 'purple'})
    ValidationError: Invalid keyword arguments:
      - person.eye_color: Value is not one of: "black", "blue", "brown", "green", "hazel", "yellow"

This raises an exception when validation fails. Alternatively, you can just obtain all of the ``Error`` objects:

.. code-block:: python

    >>> person_schema.errors({'name': 'Scott', 'height': 1.9, 'age': 25, 'eye_color': 'purple'})
    [Error(message='Value is not one of: "black", "blue", "brown", "green", "hazel", "yellow"', code='UNKNOWN', pointer='eye_color')]


Validating Function Calls
-------------------------

Another validation option is to globally define your schema and use Conformity's function decorator
`validate_call <reference.html#conformity.validator.validate_call>`_ in ``conformity.validator``. Using the same schema
as defined in the previous section, you could define a function like this:

.. code-block:: python

    @validate_call(fields.Dictionary({'person': person_schema}), returns=fields.Boolean())
    def insert_person(person):
        return True

Invoking this function would have the following results:

.. code-block:: python

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

One advantage of such an approach is that the return value is also validated. If ``insert_person`` had returned
something other than a ``bool``, that would have also resulted in a ``ValidationError``. ``validate_call`` has other
arguments, too:

.. code-block:: python

    @validate_call(args=fields.Tuple(person_schema), returns=fields.Boolean(), kwargs=None)
    def insert_person(person):
        return True

In this case, the function must be called with position arguments instead of keyword arguments (``kwargs=None`` is
required to achieve this until Conformity 2.0.0). Notice that the field wrapping the ``person_schema`` is now a
``Tuple`` instead of a ``Dictionary``, corresponding to the use of ``args`` instead of ``kwargs``.

``returns`` is an optional argument. If you omit it, the return value will not be validated.


Validating Method Calls
-----------------------

The decorator detailed in the previous section can be used only on functions unless the ``is_method=True`` is passed
to the decorator, but to prevent the need for such boilerplate, ``conformity.validator`` also has a
`validate_method <reference.html#conformity.validator.validate_method>`_ decorator:

.. code-block:: python

    class PersonRepository(GenericRepository):
        @validate_method(fields.Dictionary({'person': person_schema}), returns=fields.Boolean())
        def insert_person(person):
            return True

This will behave identically:

.. code-block:: python

    >>> repository = PersonRepository()
    >>> repository.insert_person(person={})
    ValidationError: Invalid keyword arguments:
      - person.name: Missing key: name
      - person.height: Missing key: height
      - person.age: Missing key: age
    >>> repository.insert_person(person={'name': 'Scott', 'height': 1.9, 'age': 25, 'eye_color': 'purple'})
    ValidationError: Invalid keyword arguments:
      - person.eye_color: Value is not one of: "black", "blue", "brown", "green", "hazel", "yellow"
    >>> repository.insert_person(person={'name': 'Scott', 'height': 1.9, 'age': 25, 'eye_color': 'brown'})
    True
