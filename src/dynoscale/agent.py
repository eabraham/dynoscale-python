import datetime
import os
import threading
import uuid
from enum import Enum
from pprint import pprint

from dynoscale.const.env import ENV_DEV_MODE
from dynoscale.const.header import X_REQUEST_START, X_REQUEST_ID
from dynoscale.logger import RequestLogRepository, EventLogger
from dynoscale.uploader import EventUploader
from dynoscale.utils import mock_in_heroku_headers, extract_header_value, write_header_value


class Mode(Enum):
    PRODUCTION = 1
    DEVELOPMENT = 2


class DynoscaleAgent:
    """Loads up configuration from env and provides hooks to log information necessary for scaling"""
    _instance = None

    def __init__(self):
        """Do nothing here, unless you want to overwrite some value on each instantiation.
        Initialization for this singleton has to happen in `__new__` because `__init__` is called
        on the instance that __new__ returns, which in this case is the ONLY instance there will ever be."""
        pass

    def __new__(cls):
        """DynoscaleAgent is a singleton, it will be created on first call and then same instance returned afterwards"""
        if cls._instance is None:
            print(f"thread-{threading.get_native_id()}: Creating DynoscaleAgent")
            i = super(DynoscaleAgent, cls).__new__(cls)
            # Now __init__ the instance
            i._load_config()
            i.repository = RequestLogRepository()
            i.logger = EventLogger(i.repository)
            i.uploader = EventUploader(repository=i.repository, autostart=True)
            cls._instance = i
        return cls._instance

    def _load_config(self):
        print(f"thread-{threading.get_native_id()}: _load_config")
        # print(f"{ENV_DEV_MODE} set to {os.environ.get(ENV_DEV_MODE)}")
        self.mode = Mode.DEVELOPMENT if os.environ.get(ENV_DEV_MODE) else Mode.PRODUCTION
        print(f"Dynoscale Agent started successfully in {self.mode.name} mode at {datetime.datetime.utcnow()}.")
        # TODO: What happens when unsuccessful?

    def pre_request(self, worker, req):
        print(
            f"thread-{threading.get_native_id()}: DynoscaleAgent<{id(self)}>.pre_request (w:{id(worker)} r:{id(req)})")
        if self.mode is Mode.DEVELOPMENT:
            mock_in_heroku_headers(req)
        x_request_id = extract_header_value(req, X_REQUEST_ID)
        if x_request_id is None:
            # id is necessary, create one add it to the header
            x_request_id = str(uuid.uuid4())
            write_header_value(req, X_REQUEST_ID, x_request_id)
        x_request_start = extract_header_value(req, X_REQUEST_START)
        # print(f"{X_REQUEST_START} is {x_request_start}")
        if x_request_start is not None:
            self.logger.on_request_start(x_request_id, int(x_request_start))  # TODO: Guard against parse failures
        self.logger.on_request_received(x_request_id)

    def on_exit(self, server):
        print(f"thread-{threading.get_native_id()}: DynoscaleAgent<{id(self)}on_exit (s:{id(server)})")
        self.uploader.stop()
        pprint(self.logger.repository.request_logs)  # TODO: fix this as it always prints {}, eventually remove

    def on_starting(self, server):
        print(f"thread-{threading.get_native_id()}: DynoscaleAgent<{id(self)}>.on_starting (s:{id(server)})")
        pass

    def post_request(self, worker, req, environ, resp):
        print(
            f"thread-{threading.get_native_id()}: DynoscaleAgent<{id(self)}>.post_request (s:{id(worker)} r:{id(req)} r:{id(environ)} r:{id(resp)})")
        pass

    def on_reload(self, server):
        print(
            f"thread-{threading.get_native_id()}: DynoscaleAgent<{id(self)}>.on_reload (s:{id(server)})")
        pass

    def when_ready(self, server):
        print(
            f"thread-{threading.get_native_id()}: DynoscaleAgent<{id(self)}>.when_ready (s:{id(server)})")
        pass

    def pre_fork(self, server, worker):
        print(f"thread-{threading.get_native_id()}: DynoscaleAgent<{id(self)}>.pre_fork(w:{id(worker)} s:{id(server)})")
        pass

    def post_fork(self, server, worker):
        print(
            f"thread-{threading.get_native_id()}: DynoscaleAgent<{id(self)}>.post_fork (w:{id(worker)} s:{id(server)})")
        server.log.info("Worker spawned (pid: %s)", worker.pid)
        pass

    def post_worker_init(self, worker):
        print(f"thread-{threading.get_native_id()}: DynoscaleAgent<{id(self)}>.post_worker_init (w:{id(worker)})")
        pass

    def worker_int(self, worker):
        print(f"thread-{threading.get_native_id()}: DynoscaleAgent<{id(self)}>.worker_int (w:{id(worker)})")
        pass

    def worker_abort(self, worker):
        print(f"thread-{threading.get_native_id()}: DynoscaleAgent<{id(self)}>.worker_abort (w:{id(worker)})")
        pass

    def pre_exec(self, server):
        print(f"thread-{threading.get_native_id()}: DynoscaleAgent<{id(self)}>.pre_exec ( s:{id(server)})")
        pass

    def child_exit(self, server, worker):
        print(
            f"thread-{threading.get_native_id()}: DynoscaleAgent<{id(self)}>.child_exit (w:{id(worker)} s:{id(server)})")
        pass

    def worker_exit(self, server, worker):
        print(
            f"thread-{threading.get_native_id()}: DynoscaleAgent<{id(self)}>.worker_exit (w:{id(worker)} s:{id(server)})")
        pass

    def nworkers_changed(self, server, new_value, old_value):
        print(
            f"thread-{threading.get_native_id()}: DynoscaleAgent<{id(self)}>.nworkers_changed (s:{id(server)} {old_value}->{new_value})")
        pass
