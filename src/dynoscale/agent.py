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
            i.uploader = EventUploader(repository=i.repository, autostart=False)
            cls._instance = i
        return cls._instance

    def _load_config(self):
        print(f"thread-{threading.get_native_id()}: _load_config")
        print(f"{ENV_DEV_MODE} set to {os.environ.get(ENV_DEV_MODE)}")
        self.mode = Mode.DEVELOPMENT if os.environ.get(ENV_DEV_MODE) else Mode.PRODUCTION
        print(f"Dynoscale Agent started successfully in {self.mode.name} mode at {datetime.datetime.utcnow()}.")
        # TODO: What happens when unsuccessful?

    def pre_request(self, worker, req):
        print(f"thread-{threading.get_native_id()}: pre_request")
        if self.mode is Mode.DEVELOPMENT:
            mock_in_heroku_headers(req)
        x_request_start = extract_header_value(req, X_REQUEST_START)
        x_request_id = extract_header_value(req, X_REQUEST_ID)
        if x_request_id is None:
            # id is necessary, create one add it to the header
            x_request_id = str(uuid.uuid4())
            write_header_value(req, X_REQUEST_ID, x_request_id)
        if x_request_start is not None:
            self.logger.on_request_start(x_request_id, int(x_request_start))  # TODO: Guard against parse failures
        self.logger.on_request_received(x_request_id)

    def on_exit(self, server):
        print(f"thread-{threading.get_native_id()}: on_exit")
        pprint(self.logger.repository.request_logs)  # TODO: fix this as it always prints {}, eventually remove

    def on_starting(self, server):
        pass

    def post_request(self, worker, req, environ, resp):
        pass

    def on_reload(self, server):
        pass

    def when_ready(self, server):
        pass

    def pre_fork(self, server, worker):
        pass

    def post_fork(self, server, worker):
        pass

    def post_worker_init(self, worker):
        pass

    def worker_int(self, worker):
        pass

    def worker_abort(self, worker):
        pass

    def pre_exec(self, server):
        pass

    def child_exit(self, server, worker):
        pass

    def worker_exit(self, server, worker):
        pass

    def nworkers_changed(self, server, new_value, old_value):
        pass
