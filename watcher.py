#!/usr/bin/env python3

import os
import sys
from typing import TYPE_CHECKING, Iterable
import errno
import time
import logging
import subprocess
import yaml
import pathlib
from textwrap import dedent
from argparse import ArgumentParser, Namespace

try:
    __import__('watchdog')
except:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-U', 'watchdog'])
try:
    __import__('yaml')
except:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-U', 'pyyaml'])

import yaml
from watchdog.observers.api import BaseObserver, BaseObserverSubclassCallable
from watchdog.utils import WatchdogShutdown, load_class
from watchdog.watchmedo import (
    argument,
    command,
    add_to_sys_path,
    load_config,
    _get_log_level_from_args,
    LogLevelException,
    command_parsers,
    CONFIG_KEY_TRICKS,
    epilog,
    HelpFormatter
)

from utils import set_logger


logger = logging.getLogger(__name__)
cli = ArgumentParser(epilog=epilog, formatter_class=HelpFormatter)
cli.add_argument("--version", action="version", version='0.5')
subparsers = cli.add_subparsers(dest="top_command")
command_parsers = {}

def command(args: list = [], parent: ArgumentParser = subparsers, cmd_aliases: list = []) -> callable:
    def decorator(func: callable) -> callable:
        name = func.__name__.replace("_", "-")
        desc = dedent(func.__doc__)
        parser = parent.add_parser(name, description=desc, aliases=cmd_aliases, formatter_class=HelpFormatter)
        command_parsers[name] = parser
        verbosity_group = parser.add_mutually_exclusive_group()
        verbosity_group.add_argument("-q", "--quiet", dest="verbosity", action="append_const", const=-1, help="ERROR level")
        verbosity_group.add_argument("-v", "--verbose", dest="verbosity", action="append_const", const=1, help="INFO level\n-vv: DEBUG level")
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
            parser.set_defaults(func=func)
        return func
    return decorator


def schedule_tricks_by_itself(observer: BaseObserver, tricks: Iterable, dir_path: str) -> None:
    for trick in tricks:
        for name, value in list(trick.items()):
            dirs = value.pop('dirs', [dir_path])
            recursive = value.pop('recursive', False)
            TrickClass = load_class(name)
            handler = TrickClass(**value)
            for dir in dirs:
                logger.info(f'Watching: {dir}')
                observer.schedule(handler, dir, recursive)


@command(
    [
        argument("files", nargs="*", help="trick을 정의해 둔 yaml 파일들"),
        argument('--log-file', help="로그 파일 저장 경로"),
        argument('--log-config', help="로그 설정 yaml 파일 경로"),
    ],
    cmd_aliases=["tricks"],
)
def tricks(args: Namespace) -> None:
    """
    복수의 yaml 파일에 정의된 tricks 를 한번에 실행
    """
    observers = []
    for tricks_file in args.files:
        if not os.path.exists(tricks_file):
            raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), tricks_file)
        config = load_config(tricks_file)
        try:
            tricks = config[CONFIG_KEY_TRICKS]
        except KeyError:
            raise KeyError(f"No {CONFIG_KEY_TRICKS!r} key specified in {tricks_file!r}.")

        if config.get('python_path'):
            add_to_sys_path(config['python_path'])
        force_observer = config.get('observer')
        force_interval = config.get('interval', 1)

        Observer: BaseObserverSubclassCallable
        if force_observer == 'polling':
            from watchdog.observers.polling import PollingObserver as Observer
        elif force_observer == 'kqueue':
            from watchdog.observers.kqueue import KqueueObserver as Observer
        elif (not TYPE_CHECKING and force_observer == 'winapi') or (TYPE_CHECKING and sys.platform.startswith("win")):
            from watchdog.observers.read_directory_changes import WindowsApiObserver as Observer
        elif force_observer == 'inotify':
            from watchdog.observers.inotify import InotifyObserver as Observer
        elif force_observer == 'fsevents':
            from watchdog.observers.fsevents import FSEventsObserver as Observer
        else:
            from watchdog.observers import Observer

        logger.info(f'{Observer.__name__} is selected.')

        observer = Observer(force_interval)
        dir_path = os.path.dirname(tricks_file)
        if not dir_path:
            dir_path = os.path.relpath(os.getcwd())
        schedule_tricks_by_itself(observer, tricks, dir_path)
        observer.start()
        observers.append(observer)

    try:
        while True:
            if observers:
                time.sleep(1)
            else:
                logger.warning('There is no observers...')
                break
    except WatchdogShutdown:
        for o in observers:
            o.unschedule_all()
            o.stop()
    for o in observers:
        o.join()


def main() -> None:
    """Entry-point function."""
    args = cli.parse_args()
    if args.top_command is None:
        cli.print_help()
        return 1

    try:
        log_level = _get_log_level_from_args(args)
    except LogLevelException as exc:
        print(f"Error: {exc.args[0]}", file=sys.stderr)
        command_parsers[args.top_command].print_help()
        return 1

    log_config = pathlib.Path(args.log_config) if args.log_config else pathlib.Path(__file__).parent / 'log_config.yaml'
    with log_config.open() as file:
        log_config = yaml.safe_load(file)
    set_logger(log_level, log_config, args.log_file)

    try:
        args.func(args)
    except KeyboardInterrupt:
        return 130

    return 0


if __name__ == "__main__":
    sys.exit(main())

