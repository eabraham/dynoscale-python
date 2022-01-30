import csv
import datetime
import math
import threading
import time
from io import StringIO
from threading import Thread
from typing import Optional

from dynoscale.logger import LogEvent, EventType, RequestLogRepository
from dynoscale.utils import dlog

DEFAULT_REPORT_PERIOD = 15


def logs_to_csv(logs: dict[str, list[LogEvent]]) -> str:
    """Generates a csv formatted string from logs"""
    rows = []
    for req_id, events in logs.items():
        req_start: Optional[int] = next(
            (event.event_time_ms for event in events if event.event_type == EventType.REQUEST_START),
            None
        )
        req_received: Optional[int] = next(
            (event.event_time_ms for event in events if event.event_type == EventType.REQUEST_RECEIVED),
            None
        )

        if req_start is None or req_received is None:
            continue

        req_queue_time = req_received - req_start
        rows.append((math.floor(req_start / 1000), req_queue_time, 'dyno.1', ''))
    rows = sorted(rows, key=lambda columns: columns[0])

    buffer = StringIO()
    csv_writer = csv.writer(buffer)
    csv_writer.writerows(rows)
    return buffer.getvalue()


class DynoscaleReporter:

    def __init__(
            self,
            api_url: str,
            report_period: int = DEFAULT_REPORT_PERIOD,
            autostart: bool = False,
    ):
        dlog(f"DynoscaleReporter<{id(self)}>.__init__")
        self.api_url = api_url
        self.report_period = report_period
        self.event = threading.Event()
        self.thread: Optional[threading.Thread] = None
        if autostart:
            self.start()

    def start(self):
        dlog(f"DynoscaleReporter<{id(self)}>.start")
        self.thread = Thread(target=self._upload_forever)
        self.thread.start()

    def stop(self):
        dlog(f"DynoscaleReporter<{id(self)}>.stop")
        if self.thread is not None:
            self.event.set()
            self.thread.join()
            self.thread = None

    def dump_logs(self):
        dlog(f"DynoscaleReporter<{id(self)}>.dump_logs")

    def _upload_forever(self):
        dlog(f"DynoscaleReporter<{id(self)}>._upload_forever")
        repository = RequestLogRepository()
        while True:
            if self.event.is_set():
                dlog(f"DynoscaleReporter<{id(self)}>._upload_forever")
                break
            time.sleep(self.report_period)
            logs = dict(repository.get_logs_with_event_types((EventType.REQUEST_START, EventType.REQUEST_RECEIVED)))
            payload = logs_to_csv(logs)
            dlog(f"DynoscaleReporter<{id(self)}>._upload_forever ({datetime.datetime.utcnow()})")
            self.upload_payload(payload)

    def upload_payload(self, payload: str):
        dlog(f"DynoscaleReporter<{id(self)}>.upload_payload")
        print(payload)
