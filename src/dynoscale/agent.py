import os
import uuid
from enum import Enum
from pprint import pprint

from dynoscale.const.env import ENV_DEV_MODE
from dynoscale.const.header import X_REQUEST_ID, X_REQUEST_START
from dynoscale.logger import RequestLogRepository, EventLogger
from dynoscale.uploader import EventUploader
from dynoscale.utils import dlog, mock_in_heroku_headers, extract_header_value, write_header_value


class ConfigMode(Enum):
    PRODUCTION = 1
    DEVELOPMENT = 2


class DynoscaleAgent:
    """Loads up configuration from env and provides hooks to log information necessary for scaling"""
    _instance = None

    def __init__(self):
        """Do nothing here, unless you want to overwrite some value on each instantiation.
        Initialization for this singleton has to happen in `__new__` because `__init__` is called
        on the instance that __new__ returns, which in this case is the ONLY instance there will ever be."""
        dlog(f"DynoscaleAgent<{id(self)}>.__init__")
        # This crazy condition is here only to allow typehints, actual initiation happens in config()
        if self == DynoscaleAgent._instance:
            return  # This SHOULD always return
        raise AssertionError("DynoscaleAgent isn't a singleton anymore")
        # noinspection PyUnreachableCode
        self.mode: ConfigMode = ConfigMode.DEVELOPMENT
        self.repository: RequestLogRepository = RequestLogRepository()
        self.logger: EventLogger = EventLogger(repository=self.repository)
        self.uploader: EventUploader = EventUploader(repository=self.repository)

    def __new__(cls):
        """DynoscaleAgent is a singleton, it will be created on first call and then same instance returned afterwards"""
        if cls._instance is None:
            dlog(f"DynoscaleAgent<{cls}>.__new__")
            i = super(DynoscaleAgent, cls).__new__(cls)
            # Now __init__ the instance if need be
            pass
            # Store it to class
            cls._instance = i
        # Return the one and only (per process)
        return cls._instance

    def config(self):
        dlog(f"DynoscaleAgent<{id(self)}>._load_config")
        self.mode = ConfigMode.DEVELOPMENT if os.environ.get(ENV_DEV_MODE) else ConfigMode.PRODUCTION
        dlog(f"DynoscaleAgent._load_config SUCCESS mode: {self.mode.name}")
        # TODO: What happens when unsuccessful?

        self.repository = RequestLogRepository()
        self.logger = EventLogger(self.repository)
        self.uploader = EventUploader(repository=self.repository, upload_interval=15, autostart=True)

    # Hook methods listed in order of execution
    # STARTUP: nworkers_changed, on_starting, when_ready, pre_fork (* workers) - up to here runs on server (main)
    # WORK: post_fork, post_worker_int, pre_request, post_request - these are called on workers (different process)
    # WORKER EXIT: worker_int, worker_exit - called from worker process
    # SERVER EXIT: child_exit (* workers), on_exit - called on server (main) process
    # on_reload, pre_exec, worker_abort are special :)
    def nworkers_changed(self, server, new_value, old_value):
        dlog(f"DynoscaleAgent<{id(self)}>.nworkers_changed (s:{id(server)} {old_value}->{new_value})")
        pass

    def on_starting(self, server):
        dlog(f"DynoscaleAgent<{id(self)}>.on_starting (s:{id(server)} s.pid{server.pid})")
        pass

    def when_ready(self, server):
        dlog(f"DynoscaleAgent<{id(self)}>.when_ready (s:{id(server)} s.pid{server.pid})")
        self.config()
        pass

    def pre_fork(self, server, worker):
        dlog(f"DynoscaleAgent<{id(self)}>.pre_fork (s:{id(server)} s.pid{server.pid} w:{id(worker)} w.pid{worker.pid})")

    def post_fork(self, server, worker):
        dlog(
            f"DynoscaleAgent<{id(self)}>.post_fork (s:{id(server)} s.pid{server.pid} w:{id(worker)} w.pid{worker.pid})")
        server.log.info("Worker spawned (pid: %s)", worker.pid)
        self.config()
        self.uploader.stop()
        pass

    def post_worker_init(self, worker):
        dlog(f"DynoscaleAgent<{id(self)}>.post_worker_init (w:{id(worker)} w.pid{worker.pid})")
        pass

    def pre_request(self, worker, req):
        dlog(f"DynoscaleAgent<{id(self)}>.pre_request (w:{id(worker)} w.pid{worker.pid} rq:{id(req)})")
        if self.mode is ConfigMode.DEVELOPMENT:
            mock_in_heroku_headers(req)
        x_request_id = extract_header_value(req, X_REQUEST_ID)
        if x_request_id is None:
            # id is required, create one add it to the header #TODO: Add adding id as an event?
            x_request_id = str(uuid.uuid4())
            write_header_value(req, X_REQUEST_ID, x_request_id)
        x_request_start = extract_header_value(req, X_REQUEST_START)
        if x_request_start is not None:
            self.logger.on_request_start(x_request_id, int(x_request_start))  # TODO: Guard against parse failures
        self.logger.on_request_received(x_request_id)

    def post_request(self, worker, req, environ, resp):
        dlog(
            f"DynoscaleAgent<{id(self)}>.post_request (w:{id(worker)} w.pid{worker.pid} rq:{id(req)} e:{id(environ)} rs:{id(resp)})")
        x_request_id = extract_header_value(req, X_REQUEST_ID)
        self.logger.on_request_processed(x_request_id)
        pass

    def worker_int(self, worker):
        dlog(f"DynoscaleAgent<{id(self)}>.worker_int (w:{id(worker)} w.pid{worker.pid})")
        pass

    def worker_exit(self, server, worker):
        dlog(
            f"DynoscaleAgent<{id(self)}>.worker_exit (s:{id(server)} s.pid{server.pid} w:{id(worker)} w.pid{worker.pid})")
        pass

    def child_exit(self, server, worker):
        dlog(
            f"DynoscaleAgent<{id(self)}>.child_exit (s:{id(server)} s.pid{server.pid} w:{id(worker)} w.pid{worker.pid})")
        pass

    def on_exit(self, server):
        dlog(f"DynoscaleAgent<{id(self)}>.on_exit (s:{id(server)} s.pid{server.pid})")
        self.uploader.stop()
        pprint(self.logger.repository.request_logs)  # TODO: fix this as it always prints {}, eventually remove

    def on_reload(self, server):
        dlog(f"DynoscaleAgent<{id(self)}>.on_reload (s:{id(server)} s.pid{server.pid})")
        pass

    def worker_abort(self, worker):
        dlog(f"DynoscaleAgent<{id(self)}>.worker_abort (w:{id(worker)} w.pid{worker.pid})")
        pass

    def pre_exec(self, server):
        dlog(f"DynoscaleAgent<{id(self)}>.pre_exec ( s:{id(server)} s.pid{server.pid})")
        pass
