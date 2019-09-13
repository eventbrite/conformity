Conformity Sphinx Extensions
============================

With Conformity, your class definitions are more meaningful and powerful. So, too, should be your auto-generated
documentation for those classes. Conformity includes Sphinx extensions to help you achieve the most-effective
documentation possible.

.. contents:: Contents
   :depth: 3
   :local:
   :backlinks: none


Installation
------------

Installing Conformity normally already includes the Sphinx extensions, but that does not mean they can automatically
be used. Unlike proper Conformity, Conformity's Sphinx extensions have less-lenient dependencies. You must be running
at least Python 3.6 and at least Sphinx 2.2. Once you meet these criteria, you can install Conformity normally as a
part of your documentation dependency installation.

To use the Conformity extension for Sphinx's `Autodoc`_, you'll need to have at least these two extensions configured
in your documentation ``conf.py`` file:

.. code-block:: python

    extensions = [
        ...
        'sphinx.ext.autodoc',
        ...
        'conformity.sphinx_ext.autodoc',
        ...
    ]

To use the Conformity extension for Sphinx's `Linkcode`_, you do not have to configure that extension, but you do need
to configure the standard Linkcode extension:

.. code-block:: python

    extensions = [
        ...
        'sphinx.ext.linkcode',
        ...
    ]


What do the Extensions Do?
--------------------------

Conformity's Sphinx Autodoc extension hooks in to registered `Autodoc`_ events to intercept Autodoc documentation and
modify it before it gets rendered. It looks for and does the following things:

- If a class being documented uses `Attrs`_ and the ``attr.ib`` fields have comment-based Python Type Annotations, the
  extension parses and resolves those type annotations and adds them to the documentation. It does not need to do
  anything with Python 3.6+ syntax-based Type Annotations, because Autodoc already handles those.
- If a method being documented uses comment-based Python Type Annotations for arguments or return type, the extension
  parses and resolves those type annotations and adds them to the documentation. It does not need to do anything with
  Python 3.6+ syntax-based Type Annotations, because Autodoc already handles those.
- If a class being documented extends ``Settings`` (see `Conformity Settings <settings.html>`_), the extension parses
  the schema and contents and appends documentation to the class docstring detailing the schema requirements and the
  default values.
- If a class being documented is decorated with ``@fields.ClassConfigurationSchema`` (see
  `Class Configuration Schemas <fields.html#class-configuration-schemas>`_), the extension parses the schema and
  appends documentation to the class docstring detailing the schema requirements for the constructor arguments.
- If your module has an attribute that is an instance of any Conformity field and that attribute has a docstring
  directly below it (even an empty one), the extension parses the schema of that field and appends its documentation
  to the docstring for that attribute.

The Linkcode extension does not have an events to hook in to like the Autodoc extension. Instead, it just provides a
helper method that you can use to fulfill Linkcode's ``linkcode_resolve`` attribute in ``conf.py``. Writing a
``linkcode_resolve`` function for your project often involves a lot of boilerplate code. To solve this, Conformity's
extension provides a ``create_linkcode_resolve`` function that takes several arguments and creates a function for you.
Currently, it supports only GitHub projects. To use this extension, add this to your ``conf.py``:

.. code-block:: python

    from conformity.sphinx_ext.linkcode import create_linkcode_resolve

    ...

    linkcode_resolve = create_linkcode_resolve(
        'my_github_user',
        'my_project_name',
        'my_base_module',
        my_project_version_tag_string,
    )

For example, if your GitHub the main Python module for your project is located at
``https://github.com/my_user/cool_project/project_module/__init__.py`` and you have imported ``__version__``, which
holds your project version and corresponds to the name of a tag on GitHub, you would call it like this:

.. code-block:: python

    linkcode_resolve = create_linkcode_resolve('my_user', 'cool_project', 'project_module', __version__)

The ``linkcode_resolve`` function created will try to link all source code to a ``blob/`` commit hash on GitHub, but if
it can't determine the current Git commit, it will instead use the ``tree/`` version tag as specified in the last
argument.


.. _Attrs: https://www.attrs.org/en/stable/
.. _Autodoc: https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
.. _Linkcode: https://www.sphinx-doc.org/en/master/usage/extensions/linkcode.html
