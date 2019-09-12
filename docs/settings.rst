Using Conformity Settings
=========================

In addition to `schema fields <fields.html>`_ and `simple validator tools <validators.html>`_ to use those fields,
Conformity offers a considerably more complex set of tools called Settings. This document describes Settings and how
to use them.

.. contents:: Contents
   :depth: 3
   :local:
   :backlinks: none


What Are Settings?
------------------

Conformity Settings is a tool for defining complex application settings schemas that are carefully and strictly
validated so that problems with these settings can be detected early, at application startup, rather than later on.
Originally part of `PySOA`_, Settings was moved to Conformity when its usage became prevalent outside of the context
of services. All of the code supporting Conformity Settings can be found in ``conformity.settings``.

In concept, you define settings for your application by extending
`settings.Settings <reference.html#conformity.settings.Settings>`_ and overriding its ``schema`` and ``defaults``
attributes to declare the validation rules for your settings and what defaults, if any, apply to those settings. Once
defined, you construct your extended ``Settings`` class, passing it the dictionary of configured settings, which
validates the settings according to the defined schema. You can then use the constructed ``Settings`` object as an
immutable ``Mapping``, accessing your settings as you would with any other ``Mapping``.


Creating a Settings Schema
--------------------------

The first step in creating a settings schema is to extend the ``Settings`` class. You will not override any of its
methods, but you will override its two attributes:

- ``schema``: This has type ``settings.SettingsSchema``, which is an alias for ``typing.Mapping[six.text_type, Base]``.
  Each key in this mapping is a required key in your settings, and the value is a Conformity field to validate. Any
  Conformity field is allowed, of course, so your settings can be strings, Booleans, integers, structures (lists and
  dictionaries), `ClassConfigurationSchemas <fields.rst#class-configuration-schemas>`_, and more. No key is optional,
  and extra/unknown keys are not permitted in this top-level settings dictionary (though nested dictionaries can
  permit this). However...
- ``defaults``: This has type ``settings.SettingsData``, which is an alias for
  ``typing.Mapping[six.text_type, typing.Any]``. Overriding and putting values in this field is optional, but doing so
  establishes defaults for any keys omitted from the validated settings. So while no top-level settings keys are
  optional, they can have defaults in ``defaults`` so that they aren't required to be specified. ``defaults`` also
  isn't just for top-level settings. If any of your settings fields are structures, ``defaults`` can hold nested
  default values for those structures as well. The defaults will be recursively merged with the settings values
  provided.

Furthermore, superclass schemas and defaults are inherited and merged with subclass schemas and defaults, permitting
you to define a base class of common schemas and defaults and then subclasses of non-common schemas and defaults that
inherit the common schemas and defaults. Consider this example:

.. code-block:: python

    class CommonSettings(Settings):
        schema: SettingsSchema = {
            'foo': fields.UnicodeString(),
            'bar': fields.Dictionary({
                'one': fields.UnicodeString(),
                'two': fields.List(fields.Integer()),
            }),
        }

        defaults: SettingsData = {
            'bar': {'one': 'World'},
        }

All the fields in this example – ``foo``, ``bar``, ``bar.one``, and ``bar.two`` – are required. However, ``bar`` and
``bar.one`` are defaulted, so a mapping would be valid by this ``CommonSettings`` as long as it had ``foo`` and
``bar.two``:

.. code-block:: python

    config1 = {'foo': 'Hello', 'bar': {'two': [1, 2, 3]}}  # valid
    config2 = {'foo': 'Hello', 'bar': {'one': 'Overrides default', 'two': [1, 2, 3]}}  # valid
    config3 = {}  # invalid
    config4 = {'foo': 'Hello': 'bar': {}}  # invalid

Now we extend ``CommonSettings``:

.. code-block:: python

    class ClientSettings(CommonSettings):
        schema: SettingsSchema = {
            'baz': fields.Integer(),
            'qux': fields.SchemalessDictionary(),
        }

        defaults: SettingsData = {
            'qux': {},
        }

    class ServerSettings(CommonSettings):
        schema: SettingsSchema = {
            'baz': fields.Float(),
            'qux': fields.List(fields.UnicodeString()),
        }

        defaults: SettingsData = {
            'foo': 'Default foo',
            'bar': {'one': 'Default bar.one'},
            'baz': 1.23,
        }

``ClientSettings`` in this example will have all of the settings and defaults from ``CommonSettings``, as well as
fields ``baz`` (an integer) and ``qux`` (a schemaless dictionary) and default ``qux`` (an empty dictionary).
``ServerSettings`` will also have all of the settings and defaults from ``CommonSettings``, as well as fields ``baz``
(a float) and ``qux`` (a list of strings) and defaults ``foo``, ``bar.one``, and ``baz``.

Notice that ``ServerSettings`` specified a default that overrides a default specified in ``CommonSettings``. Schemas
and defaults are inherited, but when a subclass specifies a field or default already specified in the parent, it
overrides that parent definition.

If we were to extend ``ServerSettings`` again, the new subclass would have all the settings and defaults specified in
and inherited by ``ServerSettings``, as well as whatever new settings and defaults the subclass specified. This
pattern continues and accumulates indefinitely down through the inheritance hierarchy, with the schemas and defaults
from the subclass always taking precedence over conflicting settings and schemas from its parent classes.

Multiple Inheritance
++++++++++++++++++++

First: multiple inheritance is discouraged. For many reasons, it can have unexpected and sometimes unfortunate side
effects that Conformity can't plan for or overcome. However, Conformity does its best to handle multiple inheritance.
If your ``Settings`` subclass or one of its subclasses (or so on) uses multiple inheritance, Conformity behaves as
follows:

- If a base class *is not* a subclass of ``Settings``, it is simply ignored. Conformity does not look for or care about
  any ``schema`` or ``defaults`` attributes on that class (or the absence thereof).
- If a base class *is* a subclass of ``Settings``, its ``schema`` and/or ``defaults`` (if any) will be merged with the
  ``schema`` and/or ``defaults`` (if any) from the other base classes and the current class to form the final schema
  and defaults specification. Order of precedence is handled from the rightmost base class to the leftmost base class
  in that order, just like Python method inheritance. So, for example:

  .. code-block:: python

      class ComplexSettings(SomeSettings, OtherSettings, MoreSettings, WeirdSettings):
          schema: SettingsSchema = { ... }

          defaults: SettingsData = { ... }

  In this example, Conformity will first take the effective schema and defaults from ``WeirdSettings``. Next, it will
  merge those with the schema and defaults from ``MoreSettings``, and if any conflicts exist, the items in
  ``MoreSettings`` will take precedence. It will then merge those with the schema and defaults from ``OtherSettings``
  in the same manner, and then merge those with the schema and defaults from ``SomeSettings``. At this point,
  Conformity will have the total set of inherited schema and defaults. It will then merge in the ``schema`` and
  ``defaults`` from ``ComplexSettings``, with the values from ``ComplexSettings`` taking precedence if any conflicts
  arise with the total inherited schema and defaults, and at this point the final schema and defaults for
  ``ComplexSettings`` will be complete.

If your class has a mixture of base classes that are and are not subclasses of ``Settings``, then the second rule still
applies for determining precedence, and the base classes that are not subclasses of ``Settings`` are just skipped over
and not considered.

As you can see, multiple inheritance is complicated and tricky. It can make it hard to understand what your effective
settings are, but sometimes it might just also be the only way to achieve what you need to achieve without duplicating
lots of schema. As such, we leave it to you, the developer, to determine whether to use this feature.


Using Settings Objects
----------------------

Once you've specified your settings schema and defaults, it's time to use them! ``Settings`` extends the ``Mapping``
interface, so all of the normal methods and operators you would expect to use on an immutable mapping can be used on
an instance of ``Settings``. The constructor has a single argument—a ``SettingsData`` object (just a mapping, so a
regular dictionary is fine). When you instantiate your ``Settings`` subclass, that argument is merged with the defaults
and then validated according to the schema. Any validation error raises a ``Settings.ImproperlyConfigured`` exception.

Demonstration using the example classes from the previous section:

.. code-block:: python

    config = {'foo': 'Hello', 'bar': {'two': [1, 2, 3]}, 'baz': 42}

    settings = ClientSettings(config)  # would raise `Settings.ImproperlyConfigured` if `config` was invalid

    print(settings['foo'])  # Hello
    print(settings['bar']['one'])  # World
    print(settings['bar']['two'])  # [1, 2, 3]
    print(settings['baz'])  # 42
    print(settings['qux'])  # {}


.. _PySOA: https://github.com/eventbrite/pysoa
