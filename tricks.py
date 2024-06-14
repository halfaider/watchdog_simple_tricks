import traceback
import logging
import time
from typing import Optional, Iterable

from watchdog.utils import load_class
from watchdog.tricks import Trick
from watchdog.events import (
    FileSystemEvent,
    EVENT_TYPE_MOVED,
    EVENT_TYPE_CREATED,
    EVENT_TYPE_DELETED,
    EVENT_TYPE_MODIFIED,
    EVENT_TYPE_CLOSED,
    EVENT_TYPE_OPENED
)


logger = logging.getLogger(__name__)
EVENTS = [
    EVENT_TYPE_MOVED,
    EVENT_TYPE_CREATED,
    EVENT_TYPE_DELETED,
    EVENT_TYPE_MODIFIED,
    EVENT_TYPE_CLOSED,
    EVENT_TYPE_OPENED
]


class TrickBase(Trick):

    def __init__(self, patterns: Optional[Iterable] = None,
                 ignore_patterns: Optional[Iterable] = None,
                 ignore_directories: Optional[bool] = False,
                 case_sensitive: Optional[bool] = False,
                 conduits: Optional[Iterable] = None,
                 event_interval: Optional[int] = 0) -> None:
        super(TrickBase, self).__init__(patterns, ignore_patterns, ignore_directories, case_sensitive)
        self.conduits = []
        self.event_interval = event_interval
        if conduits:
            for conduit in conduits:
                try:
                    _class = conduit.pop('class')
                    name = conduit.pop('name')
                    if not _class or not name:
                        raise Exception(f'class or name is empty.')
                except Exception as e:
                    logger.error(f'{e}')
                    continue
                events = conduit.pop('events', EVENTS)
                for event in events:
                    if event not in EVENTS:
                        logger.error(f'{event} not in {EVENTS}')
                        continue
                priority = int(conduit.pop('priority', 0))
                try:
                    conduit_cls = load_class(_class)
                    conduit_ins = conduit_cls(name, events, priority, **conduit)
                    self.conduits.append(conduit_ins)
                except Exception as e:
                    logger.error(f'Could not initiate: {name} {_class}')
                    logger.error(traceback.format_exc())
                    continue
            self.conduits.sort(key=lambda x : x.priority, reverse=True)

    def on_any_event(self, event: FileSystemEvent) -> None:
        event_dict = self.event_to_dict(event)
        for conduit in self.conduits:
            if event_dict['event_type'] not in conduit.events:
                continue
            try:
                conduit.flow(event_dict)
            except Exception:
                logger.error(traceback.format_exc())
                continue
        # sleep between events
        time.sleep(self.event_interval)

    def event_to_dict(self, event: FileSystemEvent) -> dict[str, str]:
        return {
            'event_type': event.event_type,
            'is_directory': event.is_directory,
            'src_path': event.src_path,
            'dest_path': event.dest_path,
            'is_synthetic': event.is_synthetic
        }


class SimpleTrick(TrickBase):
    pass
