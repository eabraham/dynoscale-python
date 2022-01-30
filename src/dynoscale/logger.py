import datetime
import math
import os
import time
from dataclasses import dataclass
from enum import Enum
from io import StringIO
from typing import Iterator, Tuple, Iterable

from permadict import Permadict

from dynoscale.const.env import ENV_HEROKU_DYNO
from dynoscale.utils import dlog

DEFAULT_REQUEST_LOG_DB_FILENAME: str = 'dynoscale_repo.sqlite3'


def epoch_ms():
    return math.floor(time.time_ns() / 1000_000)


class EventType(Enum):
    REQUEST_START = 10
    REQUEST_RECEIVED = 20
    REQUEST_PROCESSED = 30


@dataclass
class LogEvent:
    """Dynoscale Log Event"""
    event_time_ms: int
    event_type: EventType
    dyno: str

class EventLogger:
    """Provides the smallest subset of hooks necessary"""

    def __init__(self):
        dlog(f"EventLogger<{id(self)}>.__init__")
        self.repository = RequestLogRepository()
        self.heroku_dyno = os.environ.get(ENV_HEROKU_DYNO)

        # TODO: Here we should create a queue and spin up a thread

    def on_request_start(self, request_id: str, request_start: int):
        dlog(f"EventLogger<{id(self)}>.on_request_start")
        self.repository.add_request_event(
            request_id,
            LogEvent(request_start, EventType.REQUEST_START, self.heroku_dyno)
        )

    def on_request_received(self, request_id: str):
        dlog(f"EventLogger<{id(self)}>.on_request_received")
        self.repository.add_request_event(
            request_id,
            LogEvent(epoch_ms(), EventType.REQUEST_RECEIVED, self.heroku_dyno)
        )

    def on_request_processed(self, request_id: str):
        dlog(f"EventLogger<{id(self)}>.on_request_processed")
        self.repository.add_request_event(
            request_id,
            LogEvent(epoch_ms(), EventType.REQUEST_PROCESSED, self.heroku_dyno)
        )


def logs_to_str(request_logs: dict[str, list[LogEvent]]) -> str:
    buffer = StringIO()
    max_row_id_length = len(str(len(dict)))
    print('╔' + '=' * 99, file=buffer)
    print(F"║ Log dump of {len(dict)} from @ {datetime.datetime.utcnow()}", file=buffer)
    i = 0
    for req_id, req_events in request_logs:
        str_events = [f"{event.event_type.name}@{event.event_time_ms}" for event in req_events]
        print(f"║ {i:{max_row_id_length}} {req_id}, {', '.join(str_events)}", file=buffer)
        i += 1
    print('╚' + '=' * 99, file=buffer)
    return buffer.getvalue()


class RequestLogRepository:
    """Storage for logs regarding the lifecycle of requests"""
    # request_logs: dict[str, list[tuple[int, EventType]]]
    request_logs: Permadict

    def __init__(self,
                 repository_url: str = DEFAULT_REQUEST_LOG_DB_FILENAME
                 ):
        dlog(f"RequestLogRepository<{id(self)}>.__init__")
        self.repository_url = repository_url
        self.request_logs = Permadict(repository_url)

    def add_request_event(self, request_id: str, event: LogEvent):
        dlog(f"RequestLogRepository<{id(self)}>.add_request_event")
        req_events = self.request_logs.get(request_id, default=[])
        req_events.append(event)
        self.request_logs[request_id] = req_events
        # self.dump_logs()

    def delete_request_logs(self, request_ids: Iterable[str]):
        """Delete request logs for requests with provided request_id.
        Call this after successful upload"""
        dlog(f"RequestLogRepository<{id(self)}>.delete_request_logs")
        for key_to_delete in [key for key in self.request_logs.keys() if key in request_ids]:
            del self.request_logs[key_to_delete]

    def get_logs(self) -> Iterator[Tuple[str, list[LogEvent]]]:
        """Yield all currently stored logs"""
        for key in self.request_logs.keys():
            yield key, self.request_logs.get(key)

    def get_logs_with_event_types(self, required_event_types: iter) -> Iterator[Tuple[str, list[LogEvent]]]:
        """Yields request logs that contain at least one instance of each event type from event_types """
        for req_id, events in self.get_logs():
            missing_event_types = set(required_event_types)
            # Iterate over all request events and if an event of a required type is found remove it from the list
            # of required events (it was just found, no need to check keep looking for it) Once the set of required
            # events is empty we know that this request log contains at least one of each required event
            for event in events:
                if event.event_type in missing_event_types:
                    missing_event_types.remove(event.event_type)
                    # if there are no more missing EventTypes, this request log passes
                    if not missing_event_types:
                        yield req_id, events
                # Event of this type is either not required or was found already
            # This request does not have all required event types

    def dump_processed_logs(self):
        dlog(f"RequestLogRepository<{id(self)}>.dump_logs")
        logs = dict(self.get_logs_with_event_types({EventType.REQUEST_PROCESSED}))
        print(logs_to_str(logs))
        self.delete_request_logs(logs.keys())
