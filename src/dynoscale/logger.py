import os
import sqlite3
from typing import Tuple

from dynoscale.const.env import ENV_HEROKU_DYNO
from dynoscale.utils import dlog

DEFAULT_REQUEST_LOG_DB_FILENAME: str = 'dynoscale_repo.sqlite3'


class EventLogger:
    """Provides the smallest subset of hooks necessary"""

    def __init__(self):
        dlog(f"EventLogger<{id(self)}>.__init__")
        self.repository = RequestLogRepository()
        self.heroku_dyno = os.environ.get(ENV_HEROKU_DYNO)
        # TODO: Here we should create a queue and spin up a thread

    def on_request_received(self, timestamp: int, queue_time: int):
        dlog(f"EventLogger<{id(self)}>.on_request_received")
        self.repository.add_queue_time(timestamp, queue_time)


class RequestLogRepository:
    """Storage for logs regarding the lifecycle of requests"""

    def __init__(self,
                 filename: str = DEFAULT_REQUEST_LOG_DB_FILENAME
                 ):
        dlog(f"RequestLogRepository<{id(self)}>.__init__")
        self.filename = filename
        self.conn = sqlite3.connect(filename)
        self._create_table()

    def _create_table(self):
        with self.conn:
            self.conn.execute(
                'CREATE TABLE IF NOT EXISTS logs'
                '(timestamp INTEGER PRIMARY KEY , metric INTEGER, source STRING, metadata STRING)'
            )

    def add_queue_time(self, timestamp: int, queue_time: int):
        dlog(f"RequestLogRepository<{id(self)}>.add_request_event")
        with self.conn:
            self.conn.execute(
                'INSERT INTO logs (timestamp, metric, source, metadata) VALUES (?,?,?,?)',
                (timestamp, queue_time, "web", "")
            )

    def get_queue_times(self) -> list[Tuple[int, int, str, str]]:
        with self.conn:
            cur = self.conn.execute("SELECT timestamp, metric, source, metadata FROM logs ORDER BY timestamp ")
            return [(r[0], r[1], r[2], r[3]) for r in cur.fetchall()]

    def delete_queue_times_before(self, timestamp: int):
        dlog(f"RequestLogRepository<{id(self)}>.delete_logs_before {timestamp}")
        with self.conn:
            self.conn.execute(
                'DELETE FROM logs WHERE timestamp <?',
                (timestamp,)
            )
