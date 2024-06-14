import os
import threading
import logging

from watchdog.observers.api import BaseObserver, DEFAULT_OBSERVER_TIMEOUT, DEFAULT_EMITTER_TIMEOUT
from watchdog.observers.polling import PollingEmitter
from watchdog.utils.dirsnapshot import DirectorySnapshot, EmptyDirectorySnapshot

try:
    from utils import SimpleDirectorySnapShot
except:
    from .utils import SimpleDirectorySnapShot


logger = logging.getLogger(__name__)


class SimplePollingEmitter(PollingEmitter):

    def __init__(
        self,
        event_queue,
        watch,
        timeout=DEFAULT_EMITTER_TIMEOUT,
        event_filter=None,
        stat=os.stat,
        listdir=os.scandir,
    ):
        super(SimplePollingEmitter, self).__init__(event_queue, watch, timeout, event_filter)
        self._snapshot: DirectorySnapshot = EmptyDirectorySnapshot()
        self._lock = threading.Lock()
        self._take_snapshot = lambda: SimpleDirectorySnapShot(
            self.watch.path, self.watch.is_recursive, stat=stat, listdir=listdir, stopped_event=self.stopped_event
        )

    def on_thread_start(self) -> None:
        logger.info(f'Take first snapshot: {self.watch.path!r}')
        self._snapshot = self._take_snapshot()
        logger.info(f'{len(self._snapshot._stat_info)} directories and files: {self.watch.path!r}')

    def on_thread_stop(self) -> None:
        pass


class SimplePollingObserver(BaseObserver):

    def __init__(self, timeout=DEFAULT_OBSERVER_TIMEOUT):
        super(SimplePollingObserver, self).__init__(emitter_class=SimplePollingEmitter, timeout=timeout)

