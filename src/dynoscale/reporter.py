import csv
import datetime
import threading
import time
from io import StringIO
from threading import Thread
from typing import Optional, Iterable
from urllib.request import Request

from requests import Request, Session, PreparedRequest, Response

from dynoscale import __version__
from dynoscale.logger import RequestLogRepository
from dynoscale.utils import dlog

DEFAULT_REPORT_PERIOD = 15


def logs_to_csv(logs: Iterable[Iterable]) -> str:
    """Generates a csv formatted string from logs"""
    buffer = StringIO()
    csv_writer = csv.writer(buffer)
    csv_writer.writerows(logs)
    return buffer.getvalue()


def pprint_req(req: PreparedRequest):
    print('{}\n{}\r\n{}\r\n\r\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))


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
        self.session = Session()
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
            # TODO: be smarter about the sleep, add another loop inside and check for event more often
            # TODO: need to check more often so that when signalled to stop we don't have to wait report_period time
            time.sleep(self.report_period)
            logs_with_ids = repository.get_queue_times()
            # If there is nothing to report, exit
            if not logs_with_ids:
                dlog(
                    f"DynoscaleReporter<{id(self)}>._upload_forever ({datetime.datetime.utcnow()}) - nothing to upload")
                continue
            ids, logs = zip(*[(q[0], q[1:]) for q in logs_with_ids])
            payload = logs_to_csv(logs)
            dlog(f"DynoscaleReporter<{id(self)}>._upload_forever ({datetime.datetime.utcnow()}) - uploading")
            response = self.upload_payload(payload)
            if response and response.ok:
                repository.delete_queue_times(ids)

    def upload_payload(self, payload: str) -> Optional[Response]:
        dlog(f"DynoscaleReporter<{id(self)}>.upload_payload")
        if not payload:
            dlog(f"DynoscaleReporter<{id(self)}>.upload_payload empty payload, exiting")
            return
        headers = {
            'Content-Type': 'text/csv',
            'User-Agent': f"dynoscale-python;{__version__}",
        }

        request: Request = Request(
            method='POST',
            url=self.api_url,
            headers=headers,
            data=payload
        )
        prepared: PreparedRequest = self.session.prepare_request(request)
        pprint_req(prepared)
        response = self.session.send(prepared)
        dlog(f"DynoscaleReporter<{id(self)}>.upload_payload response status code:{response.status_code}")
        return response
