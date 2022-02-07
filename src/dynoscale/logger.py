import logging
import os
import sqlite3
from typing import Tuple, Iterable

from dynoscale.const.env import ENV_HEROKU_DYNO

logger = logging.getLogger(__name__)

DEFAULT_REQUEST_LOG_DB_FILENAME: str = 'dynoscale_repo.sqlite3'


class EventLogger:
    """Provides the smallest subset of hooks necessary"""

    def __init__(self):
        self.logger: logging.Logger = logging.getLogger(f"{logger.name}.{EventLogger.__name__}")
        self.logger.debug(f"__init__")
        self.repository = RequestLogRepository()
        self.heroku_dyno = os.environ.get(ENV_HEROKU_DYNO)
        # TODO: Here we should create a queue and spin up a thread

    def on_request_received(self, timestamp: int, queue_time: int):
        self.logger.debug(f"on_request_received")
        self.repository.add_queue_time(timestamp, queue_time)


# noinspection SqlNoDataSourceInspection,SqlResolve
class RequestLogRepository:
    """Storage for logs regarding the lifecycle of requests"""

    def __init__(self, filename: str = DEFAULT_REQUEST_LOG_DB_FILENAME):
        self.logger: logging.Logger = logging.getLogger(f"{logger.name}.{RequestLogRepository.__name__}")
        self.logger.debug(f"__init__")
        self.filename = filename
        self.conn = sqlite3.connect(filename)
        self._create_table()

    def _create_table(self):
        self.logger.debug(f"_create_table")
        with self.conn:
            self.conn.execute(
                'CREATE TABLE IF NOT EXISTS logs'
                '(timestamp INTEGER, metric INTEGER, source STRING, metadata STRING)'
            )

    def add_queue_time(self, timestamp: int, queue_time: int):
        self.logger.debug(f"add_queue_time ({timestamp},{queue_time})")
        with self.conn:
            self.conn.execute(
                'INSERT INTO logs (timestamp, metric, source, metadata) VALUES (?,?,?,?)',
                (timestamp, queue_time, "web", "")
            )

    def get_queue_times(self) -> Tuple[Tuple[int, int, int, str, str]]:
        with self.conn:
            cur = self.conn.execute("SELECT rowid, timestamp, metric, source, metadata FROM logs ORDER BY timestamp ")
            return tuple((int(r[0]), int(r[1]), int(r[2]), str(r[3]), str(r[4])) for r in cur.fetchall())

    def delete_queue_times(self, row_ids: Iterable[int]):
        self.logger.debug(f"delete_queue_times ({row_ids})")
        if not row_ids:
            return
        row_id_tuples = [(row_id,) for row_id in row_ids]
        with self.conn:
            self.conn.executemany('DELETE FROM logs WHERE rowid = (?)', row_id_tuples)
        self.vacuum()

    def delete_queue_times_before(self, time: float):
        self.logger.debug(f"delete_queue_times_before ({time})")
        with self.conn:
            self.conn.execute('DELETE FROM logs WHERE timestamp < (?)', (int(time),))
        self.vacuum()

    def vacuum(self):
        self.logger.debug(f"vacuum")
        with self.conn:
            self.conn.execute('VACUUM')
