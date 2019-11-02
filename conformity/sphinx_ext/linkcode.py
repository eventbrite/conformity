"""
An extension to the built-in Spinx extension
`sphinx.ext.linkcode <https://www.sphinx-doc.org/en/master/usage/extensions/linkcode.html>`_ to provide a more
flexible `linkcode_resolve` implementation that links to GitHub and includes source line number highlighting.

To use this extension, add the following to your Sphinx `conf.py`:

.. code-block:: python

    from conformity.sphinx_ext.linkcode import create_linkcode_resolve

    ...

    extensions = [
        ...
        'sphinx.ext.linkcode',
        ...
    ]

    ...

    linkcode_resolve = create_linkcode_resolve(
        'my_github_user',
        'my_project_name',
        'my_base_module',
        my_project_version_tag_string,
    )

isort:skip_file
"""

import importlib
import inspect
import re
import subprocess
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
)

from sphinx.application import Sphinx

from conformity import __version__


# noinspection PyCompatibility
def create_linkcode_resolve(
    github_user: str,  # noqa: E999
    github_project: str,
    top_level_module: str,
    project_version_tag: str,
) -> Callable[[str, Dict[str, Any]], str]:
    """
    Creates and returns an implementation of `linkcode_resolve` for your Sphinx `conf.py` file.

    :param github_user: The GitHub username as found right after the `https://github.com/` in the URL
    :param github_project: The GitHub project name as found right after the user name in the GitHub URL
    :param top_level_module: The top-level Python module name for your project (for example: "conformity" or "pysoa")
    :param project_version_tag: The GitHub tag name for this version of your project (if you follow a common pattern,
                                you can probably import `__version__` from your project and use that)

    :return: a function that can be assigned to `linkcode_resolve` in your `conf.py` file.
    """
    try:
        commit: Optional[str] = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('utf-8').strip()
    except subprocess.CalledProcessError:
        commit = None

    source_re = re.compile(rf'.*((site|dist)-packages|{github_project})/{top_level_module}')

    # noinspection PyCompatibility
    def linkcode_resolve(domain, info):
        if domain != 'py' or not info['module']:
            return None

        module = importlib.import_module(info['module'])
        file_name = module.__file__
        source_path = source_re.sub(top_level_module, file_name)
        where = f'blob/{commit}' if commit else f'tree/{project_version_tag}'
        suffix = ''

        attr = None
        if '.' in info['fullname']:
            obj_names = info['fullname'].split('.')
            attr = module
            obj = getattr(module, obj_names[0])
            for obj_name in obj_names:
                attr = getattr(attr, obj_name)
        else:
            obj = getattr(module, info['fullname'])

        try:
            source, start_line = inspect.getsourcelines(attr if attr else obj)
            if not (source and start_line) or start_line == 1:
                source, start_line = inspect.getsourcelines(obj)
        except (TypeError, OSError):
            try:
                source, start_line = inspect.getsourcelines(obj)
            except (TypeError, OSError):
                source, start_line = [], 0
        if source and start_line:
            suffix = f'#L{start_line}-L{start_line + len(source) - 1}'

        return (
            f'https://github.com/{github_user}/{github_project}/{where}/{source_path}{suffix}'
        )

    return linkcode_resolve


# noinspection PyUnusedLocal
def setup(app: Sphinx) -> Dict[str, Any]:
    # Do nothing, just in case someone adds this to extensions
    return {'version': __version__, 'parallel_read_safe': True}
