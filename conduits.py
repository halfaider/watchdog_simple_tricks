import time
import functools
import logging
import traceback
from pathlib import Path
from typing import Optional, Union, Any

from utils import request, parse_mappings, map_path, parse_json_response, trace_event


logger = logging.getLogger(__name__)


class ConduitBase:

    def __init__(self, name: str, events: list, priority: int) -> None:
        self.name = name
        self.events = events
        self.priority = priority

    def flow(self, event: dict[str, Union[str, bool]]) -> None:
        raise Exception('You must override this method.')


class DummyConduit(ConduitBase):

    @trace_event
    def flow(self, event: dict[str, Union[str, bool]]) -> None:
        '''override'''


class RcloneConduit(ConduitBase):

    def __init__(self, *args: tuple,
                 rc_url: str,
                 rc_user: Optional[str] = None,
                 rc_pass: Optional[str] = None,
                 vfs: Optional[str] = None,
                 mappings: Optional[list[str]] = None) -> None:
        super(RcloneConduit, self).__init__(*args)
        self.rc_url = rc_url.strip().strip('/')
        self.rc_user = rc_user.strip()
        self.rc_pass = rc_pass.strip()
        self.vfs = vfs.strip()
        self.mappings: list[tuple[str]] = parse_mappings(mappings)

    def flow(self, event: dict[str, Union[str, bool]]) -> None:
        '''override'''
        self.refresh(event.get('src_path'), event.get('is_directory'))
        if event.get('event_type') == 'moved':
            self.refresh(event.get('dest_path'), event.get('is_directory'))

    def command(method: callable) -> callable:
        @functools.wraps(method)
        def wrapper(self, *args: tuple, **kwds: dict) -> dict[str, Any]:
            command = '/'.join(method.__name__.split('__'))
            data: dict = method(self, *args, **kwds)
            logger.debug(f'{command}: {data}')
            # {'error': '', ...}
            # {'result': {'/path/to': 'Invalid...'}}
            # {'result': {'/path/to': 'OK'}}
            # {'forgotten': ['/path/to']}
            return parse_json_response(request("JSON", f'{self.rc_url}/{command}', data=data, auth=(self.rc_user, self.rc_pass)))
        return wrapper

    def get_metadata_cache(self) -> tuple[int, int]:
        result = self.vfs__stats(self.vfs).get("metadataCache", {})
        if not result:
            logger.error(f'No metadata cache statistics, assumed 0...')
        return result.get('dirs', 0), result.get('files', 0)

    @command
    def vfs__stats(self, fs: str) -> dict[str, Any]:
        return {'fs': fs}

    @command
    def vfs__refresh(self, remote_path: str, fs: str, recursive: bool = False) -> dict[str, Any]:
        return {
            'fs': fs,
            'dir': remote_path,
            'recursive': str(recursive).lower()
        }

    @command
    def operations__stat(self, remote_path: str, fs: str, opts: Optional[dict] = None) -> dict[str, Any]:
        data = {
            'fs': fs,
            'remote': remote_path,
        }
        if opts:
            data['opt'] = opts
        return data

    def is_file(self, remote_path: str) -> bool:
        result: dict = self.operations__stat(remote_path, self.vfs)
        logger.debug(result)
        item = result.get('item', {})
        return (item.get('IsDir').lower() == 'true') if item else False

    def _refresh(self, remote_path: str, fs: str, recursive: bool = False) -> dict[str, Any]:
        start_dirs, start_files = self.get_metadata_cache()
        start = time.time()
        result: dict = self.vfs__refresh(remote_path, fs, recursive)
        elapsed = time.time() - start
        dirs, files = self.get_metadata_cache()
        logger.info(f'dirs={dirs - start_dirs} files={files - start_files} elapsed={elapsed:.1f}s result="{result.get("result")!r}"')
        return result

    def refresh(self, local_path: str, is_directory: bool = False) -> None:
        remote_path = Path(map_path(local_path, self.mappings))
        parents: list[Path] = list(remote_path.parents)
        to_be_tested = str(remote_path) if is_directory else str(parents.pop(0))
        not_exists_paths = []
        result = self._refresh(to_be_tested, self.vfs)
        while result['result'].get(to_be_tested) == 'file does not exist':
            not_exists_paths.insert(0, to_be_tested)
            if parents:
                to_be_tested = str(parents.pop(0))
                result = self._refresh(to_be_tested, self.vfs)
            else:
                logger.warning(f'Hit the top-level path.')
                break
        for path in not_exists_paths:
            result = self._refresh(path, self.vfs)
            if not result.get(path) == 'OK':
                logger.error(f'Could not refresh: "{str(remote_path)}" result="{result}"')
                break


class PlexConduit(ConduitBase):

    def __init__(self, *args, plex_url: str, plex_token: str, mappings: Optional[list[str]] = None) -> None:
        super(PlexConduit, self).__init__(*args)
        self.plex_url = plex_url.strip().strip('/')
        self.plex_token = plex_token.strip()
        self.mappings: list[tuple[str]] = parse_mappings(mappings)

    def flow(self, event: dict[str, Union[str, bool]]) -> None:
        '''override'''
        if not event['is_directory']:
            self.scan(event['src_path'])
            if event.get('event_type') == 'moved':
                self.scan(event['dest_path'])

    def api(func: callable) -> callable:
        @functools.wraps(func)
        def wrapper(self, *args: tuple, **kwds: dict) -> dict[str, Any]:
            params: dict = func(self, *args, **kwds)
            key = params.pop('key', '/identity')
            method = params.pop('method', 'GET')
            params['X-Plex-Token'] = self.plex_token
            headers = {'Accept': 'application/json'}
            logger.debug(f'{key}: {params}')
            return parse_json_response(request(method, f'{self.plex_url}{key}', params=params, headers=headers))
        return wrapper

    @api
    def refresh(self, section: int, path: Optional[str] = None, force: bool = False) -> dict[str, str]:
        params = {
            'key': f'/library/sections/{section}/refresh',
            'method': 'GET',
        }
        if force:
            params['force'] = 1
        if path:
            params['path'] = path
        return params

    @api
    def sections(self) -> dict[str, str]:
        return {
            'key': '/library/sections',
            'method': 'GET'
        }

    def get_section_by_path(self, path: str) -> int:
        plex_path = Path(map_path(path, self.mappings))
        sections = self.sections()
        for directory in sections['MediaContainer']['Directory']:
            for location in directory['Location']:
                if plex_path.is_relative_to(location['path']) or \
                   Path(location['path']).is_relative_to(plex_path):
                    return int(directory['key'])

    def scan(self, path: str, force: bool = False) -> None:
        section = self.get_section_by_path(path)
        self.refresh(section, path, force)


class FFConduit(ConduitBase):

    def __init__(self, *args, ff_url: str, ff_apikey: Optional[str] = None) -> None:
        super(FFConduit, self).__init__(*args)
        self.ff_url = ff_url.strip().strip('/')
        self.ff_apikey = ff_apikey.strip()

    def flow(self, event: dict[str, Union[str, bool]]) -> None:
        '''override'''
        raise Exception('You must override this method.')

    def api(method) -> callable:
        @functools.wraps(method)
        def wrapper(self, *args: tuple, **kwds: dict) -> dict[str, Any]:
            data: dict = method(self, *args, **kwds)
            package = data.pop('package', 'system')
            command = f'{package}/api/' + '/'.join(method.__name__.split('__'))
            data['apikey'] = self.ff_apikey
            logger.debug(f'{command}: {data}')
            return parse_json_response(request('POST', f'{self.ff_url}/{command}', data=data))
        return wrapper


class PlexmateConduit(FFConduit):

    PACKAGE = 'plex_mate'

    def __init__(self, *args, mappings: Optional[list[str]] = None, **kwds) -> None:
        super(PlexmateConduit, self).__init__(*args, **kwds)
        self.mappings: list[tuple[str]] = parse_mappings(mappings)

    def flow(self, event: dict[str, Union[str, bool]]) -> None:
        '''override'''
        if not event['is_directory']:
            self.scan(event['src_path'])
            if event.get('event_type') == 'moved':
                self.scan(event['dest_path'])

    def scan(self, local_path: str) -> None:
        logger.info(f'{self.scan__do_scan(map_path(local_path, self.mappings))}')

    @FFConduit.api
    def scan__do_scan(self, dir: str) -> dict:
        return {
            'package': self.PACKAGE,
            'target': dir,
            'mode': 'ADD'
        }
