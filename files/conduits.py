import logging
from typing import Union, Optional

from conduits import ConduitBase
from utils import trace_event


logger = logging.getLogger(__name__)


class MyConduit(ConduitBase):

    def __init__(self, *args, my_setting: str, **kwds) -> None:
        super(MyConduit, self).__init__(*args, **kwds)
        self.my_setting = my_setting

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
        logger.debug(f'{self.my_setting=}')
