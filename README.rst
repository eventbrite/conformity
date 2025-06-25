Conformity - Declarative Schema for Python
==========================================

.. image:: https://readthedocs.org/projects/conformity/badge/
    :target: https://conformity.readthedocs.io

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

.. note::
   Version 2.0.0 drops support for Python 2.7 and adds official support for Python 3.12. 
   If you need Python 2.7 compatibility, please use version 1.x.

------------

Declare a schema:

.. code-block:: python

    from conformity.fields import Dictionary, Float, Integer, List, UnicodeString

    person = Dictionary({
        "name": UnicodeString(),
        "height": Float(gte=0),
        "event_ids": List(Integer(gt=0)),
    })

Check to see if data is valid:

.. code-block:: python

    data = {"name": "Andrew", "height": 180.3, "event_ids": [1, "3"]}
    errors = person.errors(data)

    # Key event_ids: Index 1: Not an integer

And wrap functions to validate on the way in and out:

.. code-block:: python

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
easily extensible (optionally via subclassing). Conformity also boasts support for full-blown application settings
schema definition and validation complete with definable defaults, and includes Sphinx ``autodoc`` extensions to help
you generate meaningful documentation for your code using Conformity.


License
-------

Conformity is licensed under the `Apache License, version 2.0 <LICENSE>`_.


Installation
------------

Conformity is available in PyPi and can be installed directly via Pip or listed in ``pyproject.toml``, ``setup.py``, ``requirements.txt``,
or ``Pipfile``. Version 2.0.0 and above requires Python 3.5 or later:

.. code-block:: bash

    pip install 'conformity~=2.0'

For modern Python projects using ``pyproject.toml``:

.. code-block:: toml

    [project]
    dependencies = [
        "conformity~=2.0",
        # other dependencies...
    ]

For ``setup.py``:

.. code-block:: python

    install_requires=[
        ...
        'conformity~=2.0',
        ...
    ]

For ``requirements.txt``:

.. code-block:: text

    conformity~=2.0

For ``Pipfile``:

.. code-block:: text

    conformity = {version="~=2.0"}


Documentation
-------------

The complete Conformity documentation is available on `Read the Docs <https://conformity.readthedocs.io>`_!
