import datetime
import math
import time
from dataclasses import dataclass
from enum import Enum

from permadict import Permadict

from dynoscale.utils import dlog


class EventType(Enum):
    X_REQUEST_START = 10
    REQUEST_RECEIVED = 20
    REQUEST_PROCESSED = 30


@dataclass
class LogEvent:
    """Dynoscale Log Event"""
    event_time_ms: int
    event_type: EventType
    value: dict


# class RequestLog:
#     request_id: int
#     request_events: list[LogEvent]
#
#     def __init__(self, request_id):
#         self.request_id = request_id
#         self.request_events = []
#
#     def append(self, request_event: LogEvent):
#         self.request_events.append(request_event)
#
#     def __repr__(self):
#         return f"{{request_id:{repr(self.request_id)}, request_events:{repr(self.request_events)}}}"
#
#
class RequestLogRepository:
    """Storage for logs regarding the lifecycle of requests"""
    # request_logs: dict[str, list[tuple[int, EventType]]]
    request_logs: Permadict

    def __init__(self):
        dlog(f"RequestLogRepository<{id(self)}>.__init__")
        self.request_logs = Permadict('dynoscale.sqlite3')

    def add_request_event(self, request_id: str, event: LogEvent):
        dlog(f"RequestLogRepository<{id(self)}>.add_request_event")
        req_events = self.request_logs.get(request_id)
        if req_events is None:
            req_events = []
        req_events.append(event)
        self.request_logs[request_id] = req_events
        # self.dump_logs()

    def delete_request_logs(self, request_ids: list):
        """Delete request logs for requests with provided request_id.
        Call this after successful upload"""
        dlog(f"RequestLogRepository<{id(self)}>.delete_request_logs")
        for key_to_delete in [key for key in self.request_logs if key in request_ids]:
            del self.request_logs[key_to_delete]

    def dump_logs(self):
        dlog(f"RequestLogRepository<{id(self)}>.dump_logs")
        print('╔' + '=' * 99)
        print(F"║ Log dump of RequestRepository:{id(self)} at {datetime.datetime.utcnow()}")
        i = 0
        request_log_items = self.request_logs.items()
        to_delete = []
        for req_id, req_events in request_log_items:

            # Filter out un-processed requests #TODO: Make sure this is not a memory leak! Since we only delete dumped
            #  requests there might be a growing number of leftovers
            if not bool([True for event in req_events if event.event_type == EventType.REQUEST_PROCESSED]):
                continue

            str_events = [f"{event.event_type.name}, {event.event_time_ms}" for event in req_events]
            print(f"║ {i:03} {req_id}, {', '.join(str_events)}")
            i += 1
            to_delete.append(req_id)
        print('╚' + '=' * 99)

        # delete
        self.delete_request_logs(to_delete)


class EventLogger:
    """Provides the smallest subset of hooks necessary"""

    def __init__(self, repository: RequestLogRepository):
        dlog(f"EventLogger<{id(self)}>.__init__")
        self.repository = repository

    def on_request_start(self, request_id: str, request_start: int):
        dlog(f"EventLogger<{id(self)}>.on_request_start")
        self.repository.add_request_event(
            request_id,
            LogEvent(request_start, EventType.X_REQUEST_START, {})
        )

    def on_request_received(self, request_id: str):
        dlog(f"EventLogger<{id(self)}>.on_request_received")
        self.repository.add_request_event(
            request_id,
            LogEvent(epoch_ms(), EventType.REQUEST_RECEIVED, {})
        )

    def on_request_processed(self, request_id: str):
        dlog(f"EventLogger<{id(self)}>.on_request_processed")
        self.repository.add_request_event(
            request_id,
            LogEvent(epoch_ms(), EventType.REQUEST_PROCESSED, {})
        )


def epoch_ms():
    return math.floor(time.time_ns() / 1000_000)
