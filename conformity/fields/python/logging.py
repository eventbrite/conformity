import collections
import logging
from typing import (
    Any,
    List,
    Mapping,
    Tuple,
)

from conformity import fields
from conformity.constants import ERROR_CODE_UNKNOWN
from conformity.types import (
    Error,
    Validation,
)


__all__ = (
    'PythonLogLevel',
    'PYTHON_LOGGER_SCHEMA',
    'PYTHON_LOGGING_CONFIG_SCHEMA',
    'PYTHON_ROOT_LOGGER_SCHEMA',
)


class PythonLogLevel(fields.Constant):
    """
    A pre-defined `Constant` field with all the possible Python log levels
    populated. All you need is a description for documentation.
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        Constructs a `PythonLogLevel` field.

        :param description: The description for documentation
        """
        super().__init__(
            logging.getLevelName(logging.DEBUG),
            logging.getLevelName(logging.INFO),
            logging.getLevelName(logging.WARNING),
            logging.getLevelName(logging.ERROR),
            logging.getLevelName(logging.CRITICAL),
            **kwargs
        )


class _LoggingValidator(fields.BaseTypeField):

    valid_type = dict
    valid_noun = 'a logging.config.dictConfig dictionary'
    introspect_type = 'logging.config.dictConfig'

    @staticmethod
    def _ensure_configured(
        source: Mapping[str, Any],
        name: str,
        validation: Validation,
        referencer_noun: str,
        referencer: str,
        referenced_noun: str,
        pointer: str,
        pointer_args: Tuple[Any, ...],
    ):
        if name not in source:
            validation.errors.append(Error(
                code=ERROR_CODE_UNKNOWN,
                message=(
                    '{referencer_noun} "{referencer}" references '
                    '{referenced_noun} "{name}", which is not configured.'
                ).format(
                    referencer_noun=referencer_noun,
                    referencer=referencer,
                    referenced_noun=referenced_noun,
                    name=name,
                ),
                pointer=pointer.format(*pointer_args),
            ))

    def validate(self, value: Any) -> Validation:
        v = super().validate(value)
        if v.errors:
            return v

        formatters = value.get('formatters', {})  # type: Mapping[str, Mapping[str, str]]
        filters = value.get('filters', {})  # type: Mapping[str, Mapping[str, Any]]
        handlers = value.get('handlers', {})  # type: Mapping[str, Mapping[str, Any]]
        loggers = value.get('loggers', {})  # type: Mapping[str, Mapping[str, Any]]
        root = value.get('root', {})  # type: Mapping[str, Any]

        if filters:
            for filter_name, filter_config in filters.items():
                standard_keys = 0
                if '()' in filter_config:
                    standard_keys = 1
                    is_standard = filter_config['()'] == 'logging.Filter'
                else:
                    is_standard = True
                if 'name' in filter_config:
                    standard_keys += 1

                if is_standard and len(filter_config) > standard_keys:
                    v.errors.append(Error(
                        code=ERROR_CODE_UNKNOWN,
                        message=(
                            'Not all keys supported for '
                            'filter named "{}"'
                        ).format(filter_name),
                        pointer='filters.{}'.format(filter_name),
                    ))

        if value.get('incremental', False) is not True:
            if handlers:
                for handler_name, handler_config in handlers.items():
                    if 'formatter' in handler_config:
                        self._ensure_configured(
                            formatters,
                            handler_config['formatter'],
                            v,
                            'Handler',
                            handler_name,
                            'formatter',
                            'handlers.{}.formatter',
                            (handler_name, ),
                        )

                    handler_filters = handler_config.get('filters', [])  # type: List[str]
                    for i, filter in enumerate(handler_filters):
                        self._ensure_configured(
                            filters,
                            filter,
                            v,
                            'Handler',
                            handler_name,
                            'filter',
                            'handlers.{}.filters.{}',
                            (handler_name, i),
                        )

            if loggers:
                for logger_name, logger_config in loggers.items():
                    logger_filters = logger_config.get('filters', [])  # type: List[str]
                    for i, filter in enumerate(logger_filters):
                        self._ensure_configured(
                            filters,
                            filter,
                            v,
                            'Logger',
                            logger_name,
                            'filter',
                            'loggers.{}.filters.{}',
                            (logger_name, i),
                        )

                    logger_handlers = logger_config.get('handlers', [])  # type: List[str]
                    for i, handler in enumerate(logger_handlers):
                        self._ensure_configured(
                            handlers,
                            handler,
                            v,
                            'Logger',
                            logger_name,
                            'handler',
                            'loggers.{}.handlers.{}',
                            (logger_name, i),
                        )

            if root:
                root_filters = root.get('filters', [])  # type: List[str]
                for i, filter in enumerate(root_filters):
                    self._ensure_configured(
                        filters,
                        filter,
                        v,
                        'Logger',
                        'root',
                        'filter',
                        'root.filters.{}',
                        (i, ),
                    )

                root_handlers = root.get('handlers', [])  # type: List[str]
                for i, handler in enumerate(root_handlers):
                    self._ensure_configured(
                        handlers,
                        handler,
                        v,
                        'Logger',
                        'root',
                        'handler',
                        'root.handlers.{}',
                        (i, ),
                    )

        return v


PYTHON_ROOT_LOGGER_SCHEMA = fields.Dictionary(
    {
        'level': PythonLogLevel(
            description=(
                'The logging level at or above which this logger will handle '
                'logging events and send them to its configured handlers.'
            ),
        ),
        'filters': fields.List(
            fields.String(),
            description=(
                'A list of references to keys from `filters` for assigning '
                'those filters to this logger.'
            ),
        ),
        'handlers': fields.List(
            fields.String(),
            description=(
                'A list of references to keys from `handlers` for assigning '
                'those handlers to this logger.'
            ),
        ),
    },
    optional_keys=('level', 'filters', 'handlers'),
)


PYTHON_LOGGER_SCHEMA = fields.Dictionary(
    PYTHON_ROOT_LOGGER_SCHEMA,
    {
        'propagate': fields.Boolean(
            description=(
                'Whether logging events handled by this logger should '
                'propagate to other loggers and/or the root logger. Defaults '
                'to `True`.'
            ),
        ),
    },
    optional_keys=('propagate', ),
)


PYTHON_LOGGING_CONFIG_SCHEMA = fields.Chain(
    fields.Dictionary(collections.OrderedDict((
        (fields.Optional('version'), fields.Integer(gte=1, lte=1)),
        (fields.Optional('formatters'), fields.Dictionary(
            (
                fields.String(),
                fields.Dictionary(
                    {
                        'format': fields.String(
                            description=(
                                'The format string for this formatter (see '
                                'https://docs.python.org/3/library/logging.html'
                                '#logrecord-attributes).'
                            ),
                        ),
                        fields.Optional('datefmt'): fields.String(
                            description=(
                                'The optional date format used when formatting '
                                'dates in the log output (see https://docs.'
                                'python.org/3/library/datetime.html'
                                '#strftime-strptime-behavior).'
                            ),
                        ),
                    },
                ),
            ),
            description=(
                'This defines a mapping of logging formatter names to '
                'formatter configurations. The `format` key specifies the log '
                'format and the `datefmt` key specifies the date format.'
            ),
        )),
        (fields.Optional('filters'), fields.Dictionary(
            (
                fields.String(),
                fields.Dictionary(
                    {
                        fields.Optional('()'): fields.TypePath(
                            base_classes=logging.Filter,
                            description=(
                                'The optional, fully-qualified name of the '
                                'class extending `logging.Filter`, used to '
                                'override the default class `logging.Filter`.'
                            ),
                        ),
                        fields.Optional('name'): fields.String(
                            description=(
                                'The optional filter name which will be passed '
                                'to the `name` argument of the '
                                '`logging.Filter` class.'
                            ),
                        ),
                    },
                    (fields.Hashable, fields.Any),
                ),
            ),
            description=(
                'This defines a mapping of logging filter names to filter '
                'configurations. If a config has only the `name` key, then '
                '`logging.Filter` will be instantiated with that argument. You '
                'can specify a `()` key (yes, really) to override the default '
                '`logging.Filter` class with a custom filter implementation '
                '(which should extend `logging.Filter`). Extra keys are '
                'allowed only for custom implementations having extra '
                'constructor arguments matching those key names.'
            ),
        )),
        (fields.Optional('handlers'), fields.Dictionary(
            (
                fields.String(),
                fields.Dictionary(
                    {
                        'class': fields.TypePath(
                            base_classes=logging.Handler,
                            description=(
                                'The fully-qualified name of the class '
                                'extending `logging.Handler`.'
                            ),
                        ),
                        fields.Optional('level'): PythonLogLevel(
                            description=(
                                'The logging level at or above which this '
                                'handler will emit logging events.'
                            ),
                        ),
                        fields.Optional('formatter'): fields.String(
                            description=(
                                'A reference to a key from `formatters` for '
                                'assigning that formatter to this handler.'
                            ),
                        ),
                        fields.Optional('filters'): fields.List(
                            fields.String(),
                            description=(
                                'A list of references to keys from `filters` '
                                'for assigning those filters to this handler.'
                            ),
                        ),
                    },
                    (fields.Hashable(), fields.Anything()),
                ),
            ),
            description=(
                'This defines a mapping of logging handler names to handler '
                'configurations. The `class` key is the importable Python path '
                'to the class extending `logging.Handler`. The `level` and '
                '`filters` keys apply to all handlers. The `formatter` key is '
                'valid for all handlers, but not all handlers will use it. '
                'Extra keys are allowed only for handlers having extra '
                'constructor arguments matching those key names.'
            ),
        )),
        (fields.Optional('loggers'), fields.Dictionary(
            (
                fields.String(),
                PYTHON_LOGGER_SCHEMA,
            ),
            description=(
                'This defines a mapping of logger names to logger '
                'configurations. A log event not handled by one of these '
                'configured loggers (if any) will instead be handled by the '
                'root logger. A log event handled by one of these configured '
                'loggers may still be handled by another logger or the root '
                'logger unless its `propagate` key is set to `False`.'
            ),
        )),
        (fields.Optional('root'), PYTHON_ROOT_LOGGER_SCHEMA),
        (fields.Optional('incremental'), fields.Boolean(
            description=(
                'Whether this configuration should be considered incremental '
                'to any existing configuration. It defaults to `False` and it '
                'is rare that you should ever need to change that.'
            ),
        )),
        (fields.Optional('disable_existing_loggers'), fields.Boolean(
            description=(
                'Whether all existing loggers (objects obtained from '
                '`logging.getLogger()`) should be disabled when this logging '
                'config is loaded. Take our advice and *always* set this to '
                '`False`. It defaults to `True` and you almost never want '
                'that, because loggers in already-loaded modules will stop '
                'working.'
            ),
        )),
    ))),
    _LoggingValidator(),
    description=(
        'Settings to enforce the standard Python logging dictionary-based '
        'configuration, as you would load with `logging.config.dictConfig()`. '
        'For more information than the documentation here, see '
        'https://docs.python.org/3/library/logging.config.html'
        '#configuration-dictionary-schema.'
    ),
)
""""""  # Empty docstring to make autodoc document this data
