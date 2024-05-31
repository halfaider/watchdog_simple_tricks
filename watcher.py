#!/usr/bin/env python3

import os
import sys
import errno
import time
import logging
import subprocess
import pathlib
import signal
import traceback
from types import FrameType
from textwrap import dedent
from argparse import ArgumentParser, Namespace
from typing import TYPE_CHECKING, Iterable, Optional

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
    command_parsers,
    CONFIG_KEY_TRICKS,
    epilog,
    HelpFormatter
)

from utils import set_logger

TERMINATION_SIGNAL = {signal.SIGTERM, signal.SIGINT}
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
                observer.schedule(handler, dir, recursive)
                logger.info(f'Watching: {dir!r}')


def get_observer(force_observer: Optional[str] = None) -> BaseObserverSubclassCallable:
    Observer: BaseObserverSubclassCallable
    match force_observer:
        case 'polling':
            #from watchdog.observers.polling import PollingObserver as Observer
            from observers import SimplePollingObserver as Observer
        case 'kqueue':
            from watchdog.observers.kqueue import KqueueObserver as Observer
        case 'inotify':
            from watchdog.observers.inotify import InotifyObserver as Observer
        case 'fsevents':
            from watchdog.observers.fsevents import FSEventsObserver as Observer
        case _:
            # TYPE_CHECKING is True, but False at runtime.
            if (not TYPE_CHECKING and force_observer == 'winapi') or (TYPE_CHECKING and sys.platform.startswith("win")):
                from watchdog.observers.read_directory_changes import WindowsApiObserver as Observer
            else:
                from watchdog.observers import Observer
    return Observer


def handler_termination_signal(_signum: int, _frame: FrameType) -> None:
    logger.info(f'Recieved signal: {_signum}')
    # Neuter all signals so that we don't attempt a double shutdown
    for signum in TERMINATION_SIGNAL:
        signal.signal(signum, signal.SIG_IGN)
    raise WatchdogShutdown


@command(
    [
        argument("files", nargs="*", help="YAML files that include tricks."),
        argument('--log-config', help="A YAML file that include logging configs."),
    ],
    cmd_aliases=["tricks"],
)
def tricks(args: Namespace) -> None:
    """
    Execute tricks in multiple yaml files.
    """
    observers = []
    try:
        for tricks_file in args.files:
            tricks_file = pathlib.Path(tricks_file)
            if not tricks_file.exists:
                raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), str(tricks_file))
            config = load_config(str(tricks_file))
            try:
                tricks = config[CONFIG_KEY_TRICKS]
            except KeyError:
                raise KeyError(f"No {CONFIG_KEY_TRICKS!r} key specified in {str(tricks_file)!r}.")
            if config.get('python_path'):
                add_to_sys_path(config['python_path'])
            force_observer = config.get('observer')
            force_timeout = config.get('timeout', 1)
            Observer: BaseObserverSubclassCallable = get_observer(force_observer)
            logger.info(f'{tricks_file.name}: {Observer.__name__}')
            observer = Observer(force_timeout)
            default_dir = tricks_file.parent.name
            if not default_dir:
                default_dir = os.path.relpath(os.getcwd())
            schedule_tricks_by_itself(observer, tricks, default_dir)
            observers.append(observer)
        for observer in observers:
            observer.start()
        while True:
            if observers:
                time.sleep(10)
            else:
                logger.warning('There are no selected observers.')
                break
    except WatchdogShutdown:
        logger.info(f'Stopping observers: {observers}')
        for o in observers:
            o.unschedule_all()
            o.stop()
            logger.debug(f'Stopped: {o}')
    for o in observers:
        o.join()
    logger.debug('Tricks ends.')


def main() -> None:
    """Entry-point function."""
    if hasattr(signal, "SIGHUP"):
        TERMINATION_SIGNAL.add(signal.SIGHUP)
    for signum in TERMINATION_SIGNAL:
        signal.signal(signum, handler_termination_signal)
    args = cli.parse_args()
    if args.top_command is None:
        cli.print_help()
        return 1
    log_config = pathlib.Path(args.log_config) if args.log_config else pathlib.Path(__file__).parent / 'example' / 'log_config.yaml'
    with log_config.open() as file:
        log_config = yaml.safe_load(file)
    set_logger(log_config)
    try:
        args.func(args)
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.error(traceback.format_exc())
