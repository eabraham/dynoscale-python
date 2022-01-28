import datetime
import threading
import time
from dataclasses import dataclass
from enum import Enum

import math

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


class RequestLog:
    request_id: int
    request_events: list

    def __init__(self, request_id):
        self.request_id = request_id
        self.request_events = []

    def append(self, request_event: LogEvent):
        self.request_events.append(request_event)

    def __repr__(self):
        return f"{{request_id:{repr(self.request_id)}, request_events:{repr(self.request_events)}}}"


class RequestLogRepository:
    """Storage for logs regarding the lifecycle of requests"""
    request_logs: dict[str, list[tuple[int, EventType]]]

    def __init__(self):
        dlog(f"RequestLogRepository<{id(self)}>.__init__")
        self.request_logs = {}

    def add_request_event(self, request_id: str, event: LogEvent):
        dlog(f"RequestLogRepository<{id(self)}>.add_request_event")
        if request_id not in self.request_logs:
            self.request_logs[request_id] = []
        self.request_logs[request_id].append((event.event_time_ms, event.event_type))
        self.dump_logs()

    def delete_request_logs(self, request_ids: list):
        """Delete request logs for requests with provided request_id.
        Call this after successful upload"""
        dlog(f"RequestLogRepository<{id(self)}>.delete_request_logs")
        for key_to_delete in [key for key in self.request_logs if key in request_ids]:
            del self.request_logs[key_to_delete]

    def dump_logs(self):
        print('╔' + '=' * 99)
        print(F"║ Log dump of RequestRepository:{id(self)} at {datetime.datetime.utcnow()}")
        i = 0
        for req_id in self.request_logs:
            str_events = [f"{event_type.name}, {event_time}" for event_time, event_type in self.request_logs[req_id]]
            print(f"║ {i:03} {req_id}, {', '.join(str_events)}")
            i += 1
        print('╚' + '=' * 99)


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
