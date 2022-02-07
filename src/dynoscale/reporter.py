import asyncio
import csv
import logging
import signal
import time
from asyncio import AbstractEventLoop
from io import StringIO
from threading import Thread
from typing import Optional, Iterable
from urllib.request import Request

from requests import Request, Session, PreparedRequest, Response

from dynoscale import __version__
from dynoscale.logger import RequestLogRepository

logger = logging.getLogger(__name__)

DEFAULT_SECONDS_BETWEEN_REPORTS = 30
DEFAULT_SECONDS_BETWEEN_DB_VACUUM = 5 * 60  # 5 minutes


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
            report_period: int = DEFAULT_SECONDS_BETWEEN_REPORTS,
            vacuum_period: int = DEFAULT_SECONDS_BETWEEN_DB_VACUUM,
            autostart: bool = False,
    ):
        self.logger: logging.Logger = logging.getLogger(f"{logger.name}.{DynoscaleReporter.__name__}")
        self.logger.debug(f"__init__")

        self.api_url = api_url
        self.report_period = report_period
        self.vacuum_period = vacuum_period
        self.repository: Optional[RequestLogRepository] = None

        self.loop: Optional[AbstractEventLoop] = None
        self.reporter_thread: Optional[Thread] = None

        self.session = Session()
        if autostart:
            self.start()

    def start(self):
        self.logger.debug(f"start")
        self.loop = asyncio.new_event_loop()
        signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
        for e_s in signals:
            self.loop.add_signal_handler(e_s, lambda e_s=e_s: asyncio.create_task(self.shutdown(e_s)))
        self.reporter_thread = Thread(target=self.loop.run_forever)
        self.reporter_thread.name = 'dynoscale-reporter'
        self.reporter_thread.start()
        asyncio.run_coroutine_threadsafe(self._reporting_coro(), self.loop)
        asyncio.run_coroutine_threadsafe(self._vacuuming_coro(), self.loop)

    def stop(self):
        self.logger.debug(f"stop")
        if self.loop:
            asyncio.run_coroutine_threadsafe(self.shutdown(), self.loop)
            if self.reporter_thread.is_alive():
                self.reporter_thread.join()

    async def shutdown(self, sig: signal.Signals = signal.SIGINT):
        self.logger.debug(f"shutdown sig:{sig.name}")
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

        for task in tasks:
            task.cancel()

        self.logger.debug(f"shutdown Canceling outstanding tasks")
        await asyncio.gather(*tasks, return_exceptions=True)
        self.loop.stop()

    async def _reporting_coro(self):
        self.logger.debug(f"_reporting_coro")
        try:
            self.repository = RequestLogRepository()
            while True:
                self.logger.debug(f"_reporting_coro - will sleep for {self.report_period}s now")
                # TODO: be smarter about the sleep, add another loop inside and check for event more often
                # TODO: need to check more often so that when signalled to stop we don't have to wait report_period time
                await asyncio.sleep(self.report_period)
                self.logger.debug(f"_reporting_coro - woke up after {self.report_period}s")
                logs_with_ids = self.repository.get_queue_times()
                # If there is nothing to report, exit
                if not logs_with_ids:
                    self.logger.debug(f"_reporting_coro - nothing to report")
                    continue
                ids, logs = zip(*[(q[0], q[1:]) for q in logs_with_ids])
                payload = logs_to_csv(logs)
                self.logger.debug(f"_reporting_coro - will report payload of length {len(logs)}")
                response = self.upload_payload(payload)
                if response and response.ok:
                    self.repository.delete_queue_times(ids)
        except asyncio.CancelledError:
            self.logger.debug(f"_reporting_coro - cancelled")

    async def _vacuuming_coro(self):
        self.logger.debug(f"_vacuuming_coro")
        try:
            while True:
                self.logger.debug(f"_vacuuming_coro - will sleep for {self.vacuum_period}s now")
                await asyncio.sleep(self.vacuum_period)
                self.logger.debug(f"_vacuuming_coro - woke up after {self.vacuum_period}s")
                self.vacuum()
        except asyncio.CancelledError:
            self.logger.debug(f"_vacuuming_coro - cancelled")

    def upload_payload(self, payload: str) -> Optional[Response]:
        self.logger.debug(f"upload_payload")
        if not payload:
            self.logger.debug(f"upload_payload  - empty payload, exiting")
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
        # pprint_req(prepared)
        response = self.session.send(prepared)
        self.logger.debug(f"upload_payload - response.status_code:{response.status_code}")
        return response

    def vacuum(self):
        self.logger.debug(f"vacuum")
        self.repository.delete_queue_times_before(time.time() - self.vacuum_period)
