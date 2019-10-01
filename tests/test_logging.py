from __future__ import (
    absolute_import,
    unicode_literals,
)

import copy
from logging import Filter
from typing import (
    Any as AnyType,
    Dict,
)

from conformity.fields.logging import PYTHON_LOGGING_CONFIG_SCHEMA


class CustomFilter(Filter):
    pass


base_test_config = {
    'version': 1,
    'formatters': {
        'console': {
            'format': '%(asctime)s %(levelname)7s %(correlation_id)s %(request_id)s: %(message)s'
        },
        'syslog': {
            'format': (
                '%(service_name)s_service: %(name)s %(levelname)s %(module)s %(process)d '
                'correlation_id %(correlation_id)s request_id %(request_id)s %(message)s'
            ),
        },
    },
    'filters': {
        'conformity_custom_filter': {
            '()': 'tests.test_logging.CustomFilter',
            'custom_argument': 'allowed',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/does/not/matter.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'console',
            'filters': ['conformity_custom_filter'],
        },
        'syslog': {
            'level': 'INFO',
            'class': 'logging.handlers.SysLogHandler',
            'formatter': 'syslog',
            'filters': ['conformity_custom_filter'],
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': False,
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'disable_existing_loggers': False,
}  # type: Dict[str, AnyType]


def test_base_test_schema_passes_validation():  # type: () -> None
    assert PYTHON_LOGGING_CONFIG_SCHEMA.errors(base_test_config) == []


def test_invalid_log_level():  # type: () -> None
    config = copy.deepcopy(base_test_config)
    config['handlers']['file']['level'] = 'NOT_A_LEVEL'

    errors = PYTHON_LOGGING_CONFIG_SCHEMA.errors(config)
    assert len(errors) == 1
    assert errors[0].code == 'UNKNOWN'
    assert errors[0].pointer == 'handlers.file.level'

    config = copy.deepcopy(base_test_config)
    config['root']['level'] = 'NOT_A_LEVEL'

    errors = PYTHON_LOGGING_CONFIG_SCHEMA.errors(config)
    assert len(errors) == 1
    assert errors[0].code == 'UNKNOWN'
    assert errors[0].pointer == 'root.level'


def test_invalid_filters():  # type: () -> None
    config = copy.deepcopy(base_test_config)
    config['filters']['test_bad_1'] = {
        'not_supported': 3,
    }

    errors = PYTHON_LOGGING_CONFIG_SCHEMA.errors(config)
    assert len(errors) == 1
    assert errors[0].code == 'UNKNOWN'
    assert errors[0].pointer == 'filters.test_bad_1'

    config = copy.deepcopy(base_test_config)
    config['filters']['test_bad_2'] = {
        '()': 'logging.Filter',
        'name': 'hello',
        'not_supported': 3,
    }

    errors = PYTHON_LOGGING_CONFIG_SCHEMA.errors(config)
    assert len(errors) == 1
    assert errors[0].code == 'UNKNOWN'
    assert errors[0].pointer == 'filters.test_bad_2'


def test_non_configured_formatters():  # type: () -> None
    config = copy.deepcopy(base_test_config)
    config['handlers']['file']['formatter'] = 'non_configured_formatter_1'

    errors = PYTHON_LOGGING_CONFIG_SCHEMA.errors(config)
    assert len(errors) == 1
    assert errors[0].code == 'UNKNOWN'
    assert errors[0].message == 'Handler "file" references formatter "non_configured_formatter_1", ' \
                                'which is not configured.'
    assert errors[0].pointer == 'handlers.file.formatter'

    config = copy.deepcopy(base_test_config)
    del config['formatters']
    del config['handlers']['syslog']['formatter']

    errors = PYTHON_LOGGING_CONFIG_SCHEMA.errors(config)
    assert len(errors) == 1
    assert errors[0].code == 'UNKNOWN'
    assert errors[0].message == 'Handler "console" references formatter "console", which is not configured.'
    assert errors[0].pointer == 'handlers.console.formatter'

    config = copy.deepcopy(base_test_config)
    config['incremental'] = True
    del config['formatters']

    assert PYTHON_LOGGING_CONFIG_SCHEMA.errors(config) == []


def test_non_configured_filters():  # type: () -> None
    config = copy.deepcopy(base_test_config)
    config['handlers']['file']['filters'] = ['non_configured_filter_1']

    errors = PYTHON_LOGGING_CONFIG_SCHEMA.errors(config)
    assert len(errors) == 1
    assert errors[0].code == 'UNKNOWN'
    assert errors[0].message == 'Handler "file" references filter "non_configured_filter_1", which is not configured.'
    assert errors[0].pointer == 'handlers.file.filters.0'

    config = copy.deepcopy(base_test_config)
    config['loggers']['django.security']['filters'] = ['non_configured_filter_2', 'conformity_custom_filter']

    errors = PYTHON_LOGGING_CONFIG_SCHEMA.errors(config)
    assert len(errors) == 1
    assert errors[0].code == 'UNKNOWN'
    assert errors[0].message == 'Logger "django.security" references filter "non_configured_filter_2", ' \
                                'which is not configured.'
    assert errors[0].pointer == 'loggers.django.security.filters.0'

    config = copy.deepcopy(base_test_config)
    config['root']['filters'] = ['conformity_custom_filter', 'non_configured_filter_3']

    errors = PYTHON_LOGGING_CONFIG_SCHEMA.errors(config)
    assert len(errors) == 1
    assert errors[0].code == 'UNKNOWN'
    assert errors[0].message == 'Logger "root" references filter "non_configured_filter_3", which is not configured.'
    assert errors[0].pointer == 'root.filters.1'

    config = copy.deepcopy(base_test_config)
    config['filters'] = {}
    config['handlers']['console']['filters'] = []
    config['handlers']['syslog']['filters'] = []
    config['loggers']['django.security']['filters'] = []
    config['root']['filters'] = ['conformity_custom_filter', 'non_configured_filter_3']

    errors = PYTHON_LOGGING_CONFIG_SCHEMA.errors(config)
    assert len(errors) == 2
    assert errors[0].code == 'UNKNOWN'
    assert errors[0].message == 'Logger "root" references filter "conformity_custom_filter", which is not configured.'
    assert errors[0].pointer == 'root.filters.0'
    assert errors[1].code == 'UNKNOWN'
    assert errors[1].message == 'Logger "root" references filter "non_configured_filter_3", which is not configured.'
    assert errors[1].pointer == 'root.filters.1'

    config = copy.deepcopy(base_test_config)
    config['incremental'] = True
    config['root']['filters'] = ['conformity_custom_filter', 'non_configured_filter_3']

    assert PYTHON_LOGGING_CONFIG_SCHEMA.errors(config) == []


def test_non_configured_handlers():  # type: () -> None
    config = copy.deepcopy(base_test_config)
    config['loggers']['django.security']['handlers'] = ['non_configured_handler_1']

    errors = PYTHON_LOGGING_CONFIG_SCHEMA.errors(config)
    assert len(errors) == 1
    assert errors[0].code == 'UNKNOWN'
    assert errors[0].message == 'Logger "django.security" references handler "non_configured_handler_1", ' \
                                'which is not configured.'
    assert errors[0].pointer == 'loggers.django.security.handlers.0'

    config = copy.deepcopy(base_test_config)
    config['root']['handlers'].append('non_configured_handler_2')

    errors = PYTHON_LOGGING_CONFIG_SCHEMA.errors(config)
    assert len(errors) == 1
    assert errors[0].code == 'UNKNOWN'
    assert errors[0].message == 'Logger "root" references handler "non_configured_handler_2", ' \
                                'which is not configured.'
    assert errors[0].pointer == 'root.handlers.1'

    config = copy.deepcopy(base_test_config)
    del config['handlers']

    errors = PYTHON_LOGGING_CONFIG_SCHEMA.errors(config)
    assert len(errors) == 2
    assert errors[0].code == 'UNKNOWN'
    assert errors[0].message == 'Logger "django.security" references handler "file", which is not configured.'
    assert errors[0].pointer == 'loggers.django.security.handlers.0'
    assert errors[1].code == 'UNKNOWN'
    assert errors[1].message == 'Logger "root" references handler "console", which is not configured.'
    assert errors[1].pointer == 'root.handlers.0'

    config = copy.deepcopy(base_test_config)
    del config['handlers']
    del config['root']

    errors = PYTHON_LOGGING_CONFIG_SCHEMA.errors(config)
    assert len(errors) == 1
    assert errors[0].code == 'UNKNOWN'
    assert errors[0].message == 'Logger "django.security" references handler "file", which is not configured.'
    assert errors[0].pointer == 'loggers.django.security.handlers.0'

    config = copy.deepcopy(base_test_config)
    del config['handlers']
    del config['loggers']

    errors = PYTHON_LOGGING_CONFIG_SCHEMA.errors(config)
    assert len(errors) == 1
    assert errors[0].code == 'UNKNOWN'
    assert errors[0].message == 'Logger "root" references handler "console", which is not configured.'
    assert errors[0].pointer == 'root.handlers.0'

    config = copy.deepcopy(base_test_config)
    config['incremental'] = True
    del config['handlers']

    assert PYTHON_LOGGING_CONFIG_SCHEMA.errors(config) == []
