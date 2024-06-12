import logging
from typing import Optional, Iterable

from watchdog.events import FileSystemEvent

from tricks import TrickBase


logger = logging.getLogger(__name__)


class MyTrick(TrickBase):

    def __init__(self, patterns: Optional[Iterable] = None,
                 ignore_patterns: Optional[Iterable] = None,
                 ignore_directories: Optional[bool] = False,
                 case_sensitive: Optional[bool] = False,
                 conduits: Optional[Iterable] = None) -> None:
        super(MyTrick, self).__init__(patterns, ignore_patterns, ignore_directories, case_sensitive, conduits)

    def on_any_event(self, event: FileSystemEvent) -> None:
        super().on_any_event(event)
