import traceback
import logging
import functools
import pathlib
import re
import subprocess
import sys
from typing import Any, Optional, Union, Iterable
from logging.config import dictConfig

try:
    __import__('requests')
except:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-U', 'requests'])

import requests


logger = logging.getLogger(__name__)


class RedactedFormatter(logging.Formatter):

    def __init__(self, *args, patterns: Iterable = [], **kwds):
        super(RedactedFormatter, self).__init__(*args, **kwds)
        self.patterns = []
        for pattern in patterns:
            self.patterns.append(re.compile(pattern))

    def format(self, record):
        msg = super().format(record)
        for pattern in self.patterns:
            msg = pattern.sub('<READACTED>', msg)
        return msg


def set_logger(level: str, log_config: dict, log_file: Optional[str] = None) -> None:
    logging_config = log_config.pop('logging')
    max_bytes = log_config.pop('max_bytes', 5242880)
    backup_count = log_config.pop('backup_count', 5)

    log_file = pathlib.Path(log_file) if log_file else None
    log_file_exists = log_file and log_file.parent.exists()
    if log_file_exists:
        logging_config['handlers']['rotating_file'] = {
            'level': level,
            'formatter': 'redacted',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': log_file,
            'mode': 'a',
            'maxBytes': max_bytes,
            'backupCount': backup_count,
        }

    for name, config in logging_config['loggers'].items():
        config['level'] = level if not name == '' else logging.NOTSET
        if log_file_exists:
            config['handlers'].append('rotating_file')

    dictConfig(logging_config)
    logger.info('log config loaded.')


def request(method: str, url: str, data: Optional[dict] = None, timeout: Union[int, tuple, None] = None, **kwds: dict) -> requests.Response:
    try:
        if method.upper() == 'JSON':
            return requests.request('POST', url, json=data or {}, timeout=timeout, **kwds)
        else:
            return requests.request(method, url, data=data, timeout=timeout, **kwds)
    except:
        tb = traceback.format_exc()
        logger.error(tb)
        response = requests.Response()
        response._content = bytes(tb, 'utf-8')
        response.status_code = 0
        return response


def parse_mappings(text: str) -> dict[str, str]:
    mappings = {}
    if text:
        settings = text.splitlines()
        for setting in settings:
            source, target = setting.split(':')
            mappings[source.strip()] = target.strip()
    return mappings


def map_path(target: str, mappings: dict) -> str:
    for k, v in mappings.items():
        target = target.replace(k, v)
    return target


def parse_json_response(response: requests.Response) -> dict[str, Any]:
    try:
        result = response.json()
    except Exception as e:
        result = {'result': response.text.strip()}
        logger.error(f'{repr(e)}: {response.text.strip()!r}')
    return result


def trace_event(func: callable) -> callable:
    @functools.wraps(func)
    def wrap(self, event):
        logger.debug(f"{self.name}.{func.__name__}(): event={event['event_type']} path={event['src_path']!r}")
        return func(self, event)
    return wrap
