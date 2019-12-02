"""
A set of extensions to the built-in Sphinx extensions `sphinx.ext.autodoc
<https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html>`_ to provide more detailed and more accurate
documentation to cover the following situations:

- Your code has type annotation comments (which `autodoc` does not detect) for backwards compatibility instead of using
  type annotation syntax (which `autodoc` does detect)
- Your code has Attrs attributes with comment-based type annotations (`autodoc` handles Attrs attributes, only detects
  their type annotations if they use annotation syntax instead of annotation comments)
- Your code uses Conformity Settings and you want to automatically document the schema and defaults (which `autodoc`
  knows nothing about)

To use this extension, add the following to your Sphinx `conf.py`:

.. code-block:: python

    extensions = [
        ...
        'sphinx.ext.autodoc',
        ...
        'conformity.sphinx_ext.autodoc',
        ...
    ]

There is no other configuration for this extension.

isort:skip_file
"""

import collections
import importlib
import inspect
import json
import logging
import os
import re
from types import (
    FunctionType,
    MethodType,
)
from typing import (
    Any,
    Callable,
    Deque,
    Dict,
    Hashable,
    Iterable,
    List,
    Mapping,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
)

from sphinx.application import Sphinx
from sphinx.config import Config

from conformity import (
    fields,
    __version__,
)
from conformity.settings import Settings


_logger = logging.getLogger(__name__)

ATTR_IB_RE = re.compile(r'(?P<argument>[a-zA-Z_]+)\s*=\s*attr\.ib\(')
REPR_AT_RE = re.compile(r'\s+at\s+0x[a-fA-F0-9]{6,}')
OPTIONAL_UNION_RE = re.compile(r'Union\[(?P<optional>[a-zA-Z0-9_.~]+),\s+NoneType\]')
PRIMITIVE_CLASS_RE = re.compile(r"<class '(?P<type>bool|int|str|bytes)'>")


class AnnotationProcessingException(Exception):
    pass


class DumbSetJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (set, frozenset)):
            return list(sorted(o))
        return super(DumbSetJsonEncoder, self).default(o)


# noinspection PyCompatibility
def get_unwrapped_arg_spec(c: Callable) -> inspect.FullArgSpec:  # noqa: E999
    while hasattr(c, '__wrapped__'):
        c = getattr(c, '__wrapped__')

    return inspect.getfullargspec(c)


# noinspection PyCompatibility
def _clean_literals(documentation: str) -> str:
    # Make all single backticks double, in reStructuredText form, but only if not part of a link (`hello`_) and not
    # already a double or triple backtick.
    new_documentation: List[str] = []

    position_to_insert_backtick = -1
    add_to_i = 0
    started = ended = is_reference = False
    last = ''
    for i, c in enumerate(documentation):
        if c == '`':
            if last == '`':
                started = ended = False
            elif started:
                ended = True
            else:
                started = True
                position_to_insert_backtick = i
                if last == ':':
                    is_reference = True
        elif ended:
            if c != '_' and not is_reference:
                new_documentation.insert(position_to_insert_backtick + add_to_i, '`')
                new_documentation.append('`')
                add_to_i += 2
            started = ended = is_reference = False

        new_documentation.append(c)
        last = c

    if (
        len(new_documentation) > 3 and
        started and
        not is_reference and
        new_documentation[-1] == '`' and
        new_documentation[-2] != '`'
    ):
        # Our code literal ended at the end of a line, so we didn't loop again to finish it off.
        new_documentation.insert(position_to_insert_backtick + add_to_i, '`')
        new_documentation.append('`')

    return ''.join(new_documentation)


# noinspection PyCompatibility
def _clean_annotation(annotation: str, scope_object: Union[Callable, Type]) -> Any:
    annotation = annotation.lstrip('*')

    while hasattr(scope_object, '__wrapped__'):
        scope_object = getattr(scope_object, '__wrapped__')

    try:
        # noinspection PyUnresolvedReferences
        scope_globals = scope_object.__globals__  # type: ignore
    except AttributeError:
        scope_globals = importlib.import_module(scope_object.__module__).__dict__
    try:
        return eval(annotation, scope_globals)
    except Exception as e:
        raise AnnotationProcessingException(
            f'Failure to evaluate `{annotation}` within the scope of scope object {scope_object} '
            f'(keys: {scope_globals.keys()}',
            *e.args,
        )


def _annotation_to_string(annotation_obj: Any) -> str:
    annotation = OPTIONAL_UNION_RE.sub(
        r'Optional[\g<optional>]',
        str(annotation_obj).replace('typing.', ''),
    ).replace('NoneType', 'None')
    return PRIMITIVE_CLASS_RE.sub(r'\g<type>', annotation)


# noinspection PyCompatibility
def get_annotations(
    arg_spec: inspect.FullArgSpec,
    function_object: Union[FunctionType, MethodType],
) -> Mapping[str, Any]:
    if arg_spec.annotations:
        return arg_spec.annotations

    try:
        source_lines = inspect.getsourcelines(function_object)[0]
    except OSError as e:
        if 'could not get source code' in e.args[0]:
            return {}
        raise

    function_started = args_started = args_finished = False
    full_type_comment: Optional[str] = None
    annotations: Dict[str, Any] = {}
    for line in source_lines:
        line = line.strip()
        if not line:
            continue

        if not function_started and line.startswith('@'):
            continue
        if not function_started and line.startswith('def'):
            function_started = True

        if function_started and not args_started:
            try:
                open_parens = line.index('(')
                line = line[open_parens + 1:]
                args_started = True
            except ValueError:
                continue

        if function_started and args_started and not args_finished:
            try:
                close_parens = line.index(')')
                line = line[close_parens + 1:].strip(')').strip()
                args_finished = True

                if line.startswith(':'):
                    line = line[1:].strip()
                if line.startswith('# type: ('):
                    full_type_comment = line
                    break
                else:
                    continue
            except ValueError:
                if '# type:' in line:
                    before_comment, type_str = line.split('# type:', 1)
                    argument_name = next(n.strip() for n in reversed(before_comment.split(',')) if n.strip())
                    argument_name = next(n.strip() for n in argument_name.split('='))
                    argument_name = argument_name.lstrip('*')
                    annotations[argument_name] = _clean_annotation(type_str, function_object)

                continue

        if function_started and args_started and args_finished and full_type_comment is None and line:
            if line.startswith('# type: ('):
                full_type_comment = line
            break

    if full_type_comment:
        full_type_comment = full_type_comment[8:].strip()
        if '->' in full_type_comment:
            before_return, return_type = full_type_comment.split('->')
            annotations['return'] = _clean_annotation(return_type.strip(), function_object)
            before_return = before_return.strip()
        else:
            before_return = full_type_comment

        if before_return != '(...)' and before_return != '()' and arg_spec.args:
            args = arg_spec.args
            if args[0] in ('self', 'cls', 'mcs', 'mcls'):
                args = args[1:]
            if arg_spec.varargs:
                args.append(f'{arg_spec.varargs}')
            if arg_spec.varkw:
                args.append(f'{arg_spec.varkw}')

            i = 0
            num_args = len(args)
            token = ''
            stack: Deque[str] = collections.deque()
            for char in before_return.strip('(').strip(')').strip():
                if i >= num_args:
                    break
                if char == ' ' and not token:
                    continue
                if char == '[':
                    stack.append(char)
                if char == ']':
                    stack.pop()
                if char == ',' and not stack:
                    annotations[args[i]] = _clean_annotation(token, function_object)
                    token = ''
                    i += 1
                else:
                    token += char
            if token and i < num_args:
                annotations[args[i]] = _clean_annotation(token, function_object)

    return annotations


def _repr_default(obj: Any) -> str:
    return REPR_AT_RE.sub('', repr(obj))


# noinspection PyCompatibility
def _pretty_type_name(t: Type) -> str:
    # moved/adapted from https://github.com/eventbrite/pysoa/blob/e44a3cc/docs/update_reference_docs.py#L381-L384
    if getattr(t, '__module__', '__builtin__') != '__builtin__':
        return '``{}.{}``'.format(t.__module__, t.__name__)
    return '``{}``'.format(t.__name__)


# noinspection PyCompatibility
def _pretty_introspect(value: fields.Base, depth: int = 1, nullable: str = '') -> str:
    # moved/adapted from https://github.com/eventbrite/pysoa/blob/e44a3cc/docs/update_reference_docs.py#L387-L500
    documentation = ''
    first = '  ' * depth
    second = '  ' * (depth + 1)
    types: Iterable[Type]

    description = _clean_literals(getattr(value, 'description', None) or '*(no description)*')

    if isinstance(value, fields.Dictionary):
        documentation += 'strict ``dict``{}: {}\n'.format(nullable, description)
        if not (value.contents or value.allow_extra_keys):
            documentation += '\nNo keys permitted.'
        iterate: Iterable[Tuple[Hashable, fields.Base]] = value.contents.items()
        if not isinstance(value.contents, collections.OrderedDict):
            iterate = sorted(value.contents.items(), key=lambda i: i[0])
        for k, v in iterate:
            documentation += '\n{}- ``{}`` - {}'.format(first, k, _pretty_introspect(v, depth + 1))
        if value.contents or not value.allow_extra_keys:
            documentation += '\n'
        if value.allow_extra_keys:
            if value.contents:
                documentation += '\n{}Extra keys of any value are allowed.'.format(first)
            else:
                documentation += '\n{}Keys of any value are allowed.'.format(first)
        if value.optional_keys:
            if value.allow_extra_keys:
                documentation += ' '
            else:
                documentation += '\n{}'.format(first)
            documentation += 'Optional keys: ``{}``\n'.format('``, ``'.join(
                sorted(map(str, value.optional_keys)),
            ))
    elif isinstance(value, fields.SchemalessDictionary):
        documentation += 'flexible ``dict``{}: {}\n'.format(nullable, description)
        documentation += '\n{}**keys**\n{}{}\n'.format(first, second, _pretty_introspect(value.key_type, depth + 1))
        documentation += '\n{}**values**\n{}{}\n'.format(first, second, _pretty_introspect(value.value_type, depth + 1))
    elif isinstance(value, (fields.List, fields.Sequence, fields.Set)):
        noun = value.introspect_type
        documentation += '``{}``{}: {}\n'.format(noun, nullable, description)
        documentation += '\n{}**values**\n{}{}\n'.format(first, second, _pretty_introspect(value.contents, depth + 1))
    elif isinstance(value, fields.Nullable):
        documentation += _pretty_introspect(value.field, depth, nullable=' (nullable)')
    elif isinstance(value, fields.Any):
        documentation += 'any of the types bulleted below{}: {}\n'.format(nullable, description)
        for v in value.options:
            documentation += '\n{}- {}'.format(first, _pretty_introspect(v, depth + 1))
        documentation += '\n'
    elif isinstance(value, fields.ClassConfigurationSchema):
        documentation += (
            'dictionary with keys ``path`` and ``kwargs`` whose ``kwargs`` schema switches based on the value of '
            '``path``, dynamically based on class imported from ``path`` (see the configuration settings schema '
            'documentation for the class named at ``path``).'
        )
        if value.description:
            documentation += ' {}'.format(description)
        if value.base_class:
            documentation += ' The imported item at the specified ``path`` must be a subclass of {}.'.format(
                _pretty_type_name(value.base_class),
            )
    elif isinstance(value, fields.PythonPath):
        documentation += (
            'a unicode string importable Python path in the format "foo.bar.MyClass", "foo.bar:YourClass.CONSTANT", '
            'etc.'
        )
        if value.description:
            documentation += ' {}'.format(description)
        if value.value_schema:
            documentation += (
                ' The imported item at the specified path must match the following schema:\n\n{}**schema**\n{}{}\n'
            ).format(first, second, _pretty_introspect(value.value_schema, depth + 1))
        elif not value.description:
            documentation += ' The imported item at the specified path can be anything.'
    elif isinstance(value, fields.TypeReference):
        types = (object, )
        if value.base_classes:
            types = (
                cast(Tuple[Type], value.base_classes) if isinstance(value.base_classes, tuple)
                else (value.base_classes, )
            )
        documentation += 'a Python ``type`` that is a subclass of the following class or classes: {}.'.format(
            ', '.join(_pretty_type_name(t) for t in types),
        )
        if value.description:
            documentation += ' {}'.format(description)
    elif isinstance(value, fields.ObjectInstance):
        types = cast(Tuple[Type], value.valid_type) if isinstance(value.valid_type, tuple) else (value.valid_type, )
        documentation += 'a Python object that is an instance of the following class or classes: {}.'.format(
            ', '.join(_pretty_type_name(t) for t in types),
        )
        if value.description:
            documentation += ' {}'.format(description)
    elif isinstance(value, fields.Polymorph):
        documentation += 'dictionary whose schema switches based on the value of key ``{}``{}: {}\n'.format(
            value.switch_field,
            nullable,
            description,
        )
        for k, v in sorted(value.contents_map.items(), key=lambda i: i[0]):
            documentation += '\n{spaces}- ``{field} == {value}`` - {doc}'.format(
                spaces=first,
                field=value.switch_field,
                value=repr(k).lstrip('u'),
                doc=_pretty_introspect(v, depth + 1),
            )
        documentation += '\n'
    else:
        introspection = value.introspect()
        documentation += '``{}``{}: {}'.format(introspection.pop('type'), nullable, description)
        introspection.pop('description', None)
        if introspection:
            documentation += ' (additional information: ``{}``)'.format(introspection)

    return documentation


# noinspection PyCompatibility
def _get_settings_schema_documentation(settings_class_object: Type[Settings]) -> List[str]:
    # moved/adapted from https://github.com/eventbrite/pysoa/blob/e44a3cc/docs/update_reference_docs.py#L518-L548
    lines = ['**Settings Schema Definition**', '']

    for k, v in sorted(settings_class_object.schema.items(), key=lambda i: i[0]):
        lines.extend('- ``{}`` - {}'.format(k, _pretty_introspect(v)).split('\n'))

    lines.append('')
    lines.append('**Default Values**')
    lines.append('')
    lines.append(
        'Keys present in the dict below can be omitted from compliant settings dicts, '
        'in which case the values below will apply as the default values.',
    )
    lines.append('')
    lines.append('.. code-block:: json')
    lines.append('')

    for line in json.dumps(
        settings_class_object.defaults,
        ensure_ascii=False,
        indent=4,
        sort_keys=True,
        cls=DumbSetJsonEncoder,
    ).split('\n'):
        lines.append('    {}'.format(line.rstrip()))

    return lines


# noinspection PyCompatibility
def _get_class_schema_documentation(class_object: Type) -> List[str]:
    # moved/adapted from https://github.com/eventbrite/pysoa/blob/e44a3cc/docs/update_reference_docs.py#L556-L572
    lines = ['**Class Configuration Schema**', '']

    field: fields.Base = getattr(class_object, '_conformity_initialization_schema')
    lines.extend(_pretty_introspect(field, depth=0).split('\n'))

    return lines


# noinspection PyCompatibility,PyUnusedLocal
def autodoc_process_docstring(app: Sphinx, what: str, name: str, obj: Any, options: Any, lines: List[str]) -> None:
    for i, line in enumerate(lines):
        if line.strip() == 'isort:skip_file':
            lines[i] = ''
        else:
            lines[i] = _clean_literals(line)

    if inspect.isclass(obj):
        if issubclass(obj, Settings):
            # moved/adapt from https://github.com/eventbrite/pysoa/blob/e44a3cc/docs/update_reference_docs.py#L748-L749
            lines.extend(['', ''])
            lines.extend(_get_settings_schema_documentation(obj))
        elif hasattr(obj, '_conformity_initialization_schema'):
            # move/adapt from https://github.com/eventbrite/pysoa/blob/e44a3cc/docs/update_reference_docs.py#L753-L759
            lines.extend(['', ''])
            lines.extend(_get_class_schema_documentation(obj))
    elif what == 'data' and isinstance(obj, fields.Base):
        lines.extend(['', ''])
        lines.extend(_pretty_introspect(obj, depth=0).split('\n'))


# noinspection PyCompatibility,PyUnusedLocal
def autodoc_process_signature(
    app: Sphinx,
    what: str,
    name: str,
    obj: Any,
    options: Any,
    signature: Optional[str],
    return_annotation: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    if what == 'data' and isinstance(obj, fields.Base):
        return ' = pre-defined Conformity schema {}'.format(name), None

    original_signature = signature
    original_return_annotation = return_annotation

    annotations: Mapping[str, Any] = {}
    arg_spec = None
    is_class = inspect.isclass(obj)

    if is_class and hasattr(obj, '__attrs_attrs__'):
        init = getattr(obj, '__init__')
        arg_spec = get_unwrapped_arg_spec(init)
        if arg_spec.annotations and len(arg_spec.annotations) > 1:
            annotations = arg_spec.annotations
        else:
            attrib_name = ''
            paren_stack: Deque[str] = collections.deque()
            for line in inspect.getsourcelines(obj)[0]:
                line = line.strip()
                if not line:
                    continue

                if not paren_stack:
                    match = ATTR_IB_RE.match(line)
                    if match:
                        attrib_name = match.group('argument')
                        paren_stack.append('(')
                        line = line[match.end():]

                if paren_stack:
                    for i, c in enumerate(line):
                        if c == '(':
                            paren_stack.append('(')
                        elif c == ')':
                            paren_stack.pop()

                        if not paren_stack:
                            # We're done defining the attr
                            line = line[i + 1:].strip()
                            if line.startswith('# type: '):
                                cast(Dict, annotations)[attrib_name] = _clean_annotation(line[8:], obj)

            cast(Dict, annotations).pop('', None)
            if not annotations:
                annotations = get_annotations(arg_spec, init)
        if annotations:
            init.__annotations__ = annotations

    if inspect.isfunction(obj) or inspect.ismethod(obj):
        arg_spec = get_unwrapped_arg_spec(obj)
        annotations = get_annotations(arg_spec, obj)

        if 'return' in annotations:
            return_annotation = _annotation_to_string(annotations['return'])

    if arg_spec and annotations and (len(annotations) > 1 or 'return' not in annotations) and (
        not signature or ':' not in signature or signature.count(':') == signature.count('lambda')
    ):
        args = [a for a in arg_spec.args if a not in ('self', 'cls', 'mcs', 'mcls')]
        num_args = len(args)
        num_defaults = len(arg_spec.defaults) if arg_spec.defaults else 0
        first_default_index = num_args - num_defaults

        has_put_arg = False
        has_put_vararg = False
        new_signature = '('
        for i, arg in enumerate(args):
            if has_put_arg:
                new_signature += ', '
            has_put_arg = True
            new_signature += arg
            if arg in annotations:
                new_signature += f': {_annotation_to_string(annotations[arg])}'
            if i >= first_default_index:
                new_signature += ' = ' if arg in annotations else '='
                new_signature += _repr_default(cast(Tuple[Any, ...], arg_spec.defaults)[i - first_default_index])

        if arg_spec.varargs and not has_put_vararg:
            if has_put_arg:
                new_signature += ', '
            has_put_arg = True
            arg_name = f'{arg_spec.varargs}'
            annotation = f': {_annotation_to_string(annotations[arg_name])}' if arg_name in annotations else ''
            new_signature += f'*{arg_name}{annotation}'

        for arg in arg_spec.kwonlyargs:
            if has_put_arg:
                new_signature += ', '
            has_put_arg = True
            annotation = f': {_annotation_to_string(annotations[arg])}' if arg in annotations else ''
            new_signature += f'{arg}{annotation}'
            if arg_spec.kwonlydefaults and arg in arg_spec.kwonlydefaults:
                new_signature += f' = {_repr_default(arg_spec.kwonlydefaults[arg])}'

        if arg_spec.varkw:
            if has_put_arg:
                new_signature += ', '
            arg_name = f'{arg_spec.varkw}'
            annotation = f': {_annotation_to_string(annotations[arg_name])}' if arg_name in annotations else ''
            new_signature += f'**{arg_name}{annotation}'

        new_signature += ')'

        signature = new_signature

    if return_annotation and signature and signature.endswith(' -> None'):
        signature = signature[:-8]

    if signature != original_signature or return_annotation != original_return_annotation:
        _logger.warning(
            f'Rewriting signature for "{name}"" from `{original_signature} -> {original_return_annotation}` to '
            f'`{signature} -> {return_annotation}`'
        )

    return signature, return_annotation


def config_initialized(app: Sphinx, config: Config) -> None:
    config.html_static_path.append(os.path.join(os.path.dirname(__file__), 'static'))
    app.add_js_file('autodoc_auto_toc.js')


def setup(app: Sphinx) -> Dict[str, Any]:
    app.connect('autodoc-process-docstring', autodoc_process_docstring)
    app.connect('autodoc-process-signature', autodoc_process_signature)
    app.connect('config-inited', config_initialized)

    return {'version': __version__, 'parallel_read_safe': True}
