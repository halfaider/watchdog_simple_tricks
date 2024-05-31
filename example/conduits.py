from typing import Union

from conduits import ConduitBase
from utils import trace_event


class MyConduit(ConduitBase):

    def __init__(self, name: str, events: list, priority: int) -> None:
        super(MyConduit, self).__init__(name, events, priority)

    @trace_event
    def flow(self, event: dict[str, Union[str, bool]]) -> None:
        '''
        'event_type': 'moved' | 'created' | 'deleted' | 'modified' | 'closed' | 'opened'
        'is_directory': True | False
        'src_path': str
        'dest_path': str
        'is_synthetic': True | False
        }
        '''
        pass
