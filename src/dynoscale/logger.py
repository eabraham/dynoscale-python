import math
import threading
import time
from dataclasses import dataclass
from enum import Enum
from pprint import pprint


class EventType(Enum):
    X_REQUEST_START = 10
    REQUEST_RECEIVED = 20


@dataclass
class Event:
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

    def append(self, request_event: Event):
        self.request_events.append(request_event)

    def __repr__(self):
        return f"{{request_id:{repr(self.request_id)}, request_events:{repr(self.request_events)}}}"


class RequestLogRepository:
    """Storage for logs regarding the lifecycle of requests"""
    request_logs: dict

    def __init__(self):
        print(f"thread-{threading.get_native_id()}: Initializing RequestLogRepository")
        self.request_logs = {}

    def add_request_event(self, request_id: str, event: Event):
        print(f"thread-{threading.get_native_id()}: RequestLogRepository.add_request_event")
        if request_id not in self.request_logs:
            self.request_logs[request_id] = RequestLog(request_id)
        request_log = self.request_logs[request_id]
        request_log.append(event)
        pprint(self.request_logs)

    def delete_request_logs(self, request_ids: list):
        """Delete request logs for requests with provided request_id.
        Call this after successful upload"""
        print(f"thread-{threading.get_native_id()}: RequestLogRepository.delete_request_logs")
        for key_to_delete in [key for key in self.request_logs if key in request_ids]:
            del self.request_logs[key_to_delete]


class EventLogger:
    """Provides the smallest subset of hooks necessary"""

    def __init__(self, repository: RequestLogRepository):
        print(f"thread-{threading.get_native_id()}: Initializing EventLogger")
        self.repository = repository

    def on_request_start(self, request_id: str, request_start: int):
        print(f"thread-{threading.get_native_id()}: EventLogger.on_request_start")
        self.repository.add_request_event(
            request_id,
            Event(request_start, EventType.X_REQUEST_START, {})
        )

    def on_request_received(self, request_id: str):
        print(f"thread-{threading.get_native_id()}: EventLogger.on_request_received")
        self.repository.add_request_event(
            request_id,
            Event(epoch_ms(), EventType.REQUEST_RECEIVED, {})
        )


def epoch_ms():
    return math.floor(time.time_ns() / 1000_000)