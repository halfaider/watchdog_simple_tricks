import traceback
import logging
import functools
import threading
import re
import subprocess
import sys
import os
import errno
from stat import S_ISDIR
from typing import Any, Optional, Union, Iterable, Callable, Tuple, Iterator
from logging.config import dictConfig

from watchdog.utils.dirsnapshot import DirectorySnapshot

try:
    __import__('requests')
except:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-U', 'requests'])

import requests


logger = logging.getLogger(__name__)


class RedactedFormatter(logging.Formatter):

    def __init__(self, *args, patterns: Iterable = [], substitute: str = '<REDACTED>', **kwds):
        super(RedactedFormatter, self).__init__(*args, **kwds)
        self.patterns = []
        self.substitute = substitute
        for pattern in patterns:
            self.patterns.append(re.compile(pattern))

    def format(self, record):
        msg = super().format(record)
        for pattern in self.patterns:
            match = pattern.search(msg)
            if match:
                if len(match.groups()) > 0:
                    groups = list(match.groups())
                else:
                    groups = [match.group(0)]
                for found in groups:
                    msg = self.redact(re.compile(found), msg)
        return msg

    def redact(self, pattern: re.Pattern, text: str) -> str:
        return pattern.sub(self.substitute, text)


class SimpleDirectorySnapShot(DirectorySnapshot):

    def __init__(
        self,
        path: str,
        recursive: bool = True,
        stat: Callable[[str], os.stat_result] = os.stat,
        listdir: Callable[[Optional[str]], Iterator[os.DirEntry]] = os.scandir,
        stopped_event: threading.Event = None,
    ):
        self.recursive = recursive
        self.stat = stat
        self.listdir = listdir
        self._stopped_event = stopped_event

        self._stat_info: dict[str, os.stat_result] = {}
        self._inode_to_path: dict[Tuple[int, int], str] = {}

        st = self.stat(path)
        self._stat_info[path] = st
        self._inode_to_path[(st.st_ino, st.st_dev)] = path

        for p, st in self.walk(path):
            if not self.should_keep_running: break
            i = (st.st_ino, st.st_dev)
            self._inode_to_path[i] = p
            self._stat_info[p] = st

    @property
    def should_keep_running(self):
        return not self._stopped_event.is_set()

    def walk(self, root: str) -> Iterator[Tuple[str, os.stat_result]]:
        if not self.should_keep_running: return
        try:
            paths = [os.path.join(root, entry.name) for entry in self.listdir(root)]
        except OSError as e:
            # Directory may have been deleted between finding it in the directory
            # list of its parent and trying to delete its contents. If this
            # happens we treat it as empty. Likewise if the directory was replaced
            # with a file of the same name (less likely, but possible).
            if e.errno in (errno.ENOENT, errno.ENOTDIR, errno.EINVAL):
                return
            else:
                raise

        entries = []
        for p in paths:
            if not self.should_keep_running: break
            try:
                entry = (p, self.stat(p))
                entries.append(entry)
                yield entry
            except OSError:
                continue

        if self.recursive:
            for path, st in entries:
                if not self.should_keep_running: break
                try:
                    if S_ISDIR(st.st_mode):
                        for entry in self.walk(path):
                            if not self.should_keep_running: break
                            yield entry
                except PermissionError:
                    pass


def set_logger(log_config: dict) -> None:
    filename = log_config['handlers']['default_file_handler']['filename']
    if not filename:
        log_config['handlers'].pop('default_file_handler', None)
    for config in log_config['loggers'].values():
        if not filename and 'default_file_handler' in config['handlers']:
            config['handlers'].remove('default_file_handler')
        elif filename and 'default_file_handler' not in config['handlers']:
            config['handlers'].append('default_file_handler')
    dictConfig(log_config)
    logger.info('logging config is loaded.')


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


def parse_json_response(response: requests.Response) -> dict[str, Any]:
    try:
        result = response.json()
    except Exception as e:
        result = {
            'status_code': response.status_code,
            'content': response.text.strip(),
            'exception': f'{repr(e)}',
        }
    return result


def parse_mappings(mappings: Iterable[str]) -> list[tuple[str]]:
    return [tuple(mapping.split(':')) for mapping in mappings]


def map_path(target: str, mappings: Iterable[Iterable[str]]) -> str:
    for mapping in mappings:
        target = target.replace(mapping[0], mapping[1])
    return target


def trace_event(func: callable) -> callable:
    @functools.wraps(func)
    def wrap(self, event):
        logger.debug(f"{self.name}.{func.__name__}(): event={event['event_type']} path={event['src_path']!r}")
        return func(self, event)
    return wrap
