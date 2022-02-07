import logging
import os
from enum import Enum

from dynoscale.const.env import ENV_DEV_MODE, ENV_DYNOSCALE_URL
from dynoscale.const.header import X_REQUEST_START
from dynoscale.logger import EventLogger
from dynoscale.reporter import DynoscaleReporter
from dynoscale.utils import mock_in_heroku_headers, extract_header_value, epoch_ms

logger = logging.getLogger(__name__)

class ConfigMode(Enum):
    PRODUCTION = 1
    DEVELOPMENT = 2


class AgentRole(Enum):
    SERVER = 1
    WORKER = 2


class DynoscaleAgent:
    """Loads up configuration from env and provides hooks to log information necessary for scaling"""
    _instance = None

    @property
    def role(self) -> AgentRole:
        return self._role

    @role.setter
    def role(self, value: AgentRole):
        if value is AgentRole.SERVER:
            self.event_logger = EventLogger()
            self.reporter = DynoscaleReporter(
                api_url=self.api_url,
            )
            self.reporter.start()
        elif value is AgentRole.WORKER:
            self.reporter.stop()
            self.reporter = None
            self.event_logger = EventLogger()
        self._role = value

    def __init__(self):
        """Do nothing here, unless you want to overwrite some value on each instantiation.
        Initialization for this singleton has to happen in `__new__` because `__init__` is called
        on the instance that __new__ returns, which in this case is the ONLY instance there will ever be."""
        self.logger.debug(f"__init__")
        # This crazy condition is here only to allow typehints, actual initiation happens in config()
        if self == DynoscaleAgent._instance:
            return  # This SHOULD always return
        raise AssertionError("DynoscaleAgent isn't a singleton anymore")
        # noinspection PyUnreachableCode
        self.logger: logging.Logger = logging.getLogger(f"{logger.name}.{DynoscaleAgent.__name__}")
        self.mode: ConfigMode = ConfigMode.DEVELOPMENT
        self.role: AgentRole = AgentRole.SERVER
        self.api_url: str = ""
        self.event_logger: EventLogger = EventLogger()
        # self.uploader: EventUploader = EventUploader(repository=self.repository)
        self.reporter: Optional[DynoscaleReporter] = None

    def __new__(cls):
        """DynoscaleAgent is a singleton, it will be created on first call and then same instance returned afterwards"""
        if cls._instance is None:
            i = super(DynoscaleAgent, cls).__new__(cls)
            # Now __init__ the instance if need be
            i.logger: logging.Logger = logging.getLogger(f"{logger.name}.{DynoscaleAgent.__name__}")
            i.logger.debug(f"__new__")
            # TODO: if env['DYNO'] isn't dyno.1 then don't upload or log anything, basically remove itself.
            i._role = AgentRole.SERVER
            # Store it to class
            cls._instance = i
        # Return the one and only (per process)
        return cls._instance

    def config(self):
        self.logger.debug(f"_load_config")
        self.mode = ConfigMode.DEVELOPMENT if os.environ.get(ENV_DEV_MODE) else ConfigMode.PRODUCTION
        self.api_url = os.environ.get(ENV_DYNOSCALE_URL)
        self.logger.debug(f"_load_config SUCCESS mode: {self.mode.name}")
        # TODO: What happens when unsuccessful?

        self.event_logger = EventLogger()
        self.reporter = DynoscaleReporter(api_url=self.api_url, autostart=True)

    # Hook methods listed in order of execution
    # STARTUP: nworkers_changed, on_starting, when_ready, pre_fork (* workers) - up to here runs on server (main)
    # WORK: post_fork, post_worker_int, pre_request, post_request - these are called on workers (different process)
    # WORKER EXIT: worker_int, worker_exit - called from worker process
    # SERVER EXIT: child_exit (* workers), on_exit - called on server (main) process
    # on_reload, pre_exec, worker_abort are special :)
    def nworkers_changed(self, server, new_value, old_value):
        self.logger.debug(f"nworkers_changed (s:{id(server)} {old_value}->{new_value})")

    def on_starting(self, server):
        self.logger.debug(f"on_starting (s:{id(server)} s.pid{server.pid})")

    def when_ready(self, server):
        self.logger.debug(f"when_ready (s:{id(server)} s.pid{server.pid})")
        self.config()

    def pre_fork(self, server, worker):
        self.logger.debug(f"pre_fork (s:{id(server)} s.pid{server.pid} w:{id(worker)} w.pid{worker.pid})")

    def post_fork(self, server, worker):
        self.logger.debug(
            f"post_fork (s:{id(server)} s.pid{server.pid} w:{id(worker)} w.pid{worker.pid})")
        server.log.info("Worker spawned (pid: %s)", worker.pid)
        self.role = AgentRole.WORKER

    def post_worker_init(self, worker):
        self.logger.debug(f"post_worker_init (w:{id(worker)} w.pid{worker.pid})")

    def pre_request(self, worker, req):
        self.logger.debug(f"pre_request (w:{id(worker)} w.pid{worker.pid} rq:{id(req)})")
        req_received = epoch_ms()
        if self.mode is ConfigMode.DEVELOPMENT:
            mock_in_heroku_headers(req)
        x_request_start = extract_header_value(req, X_REQUEST_START)
        if x_request_start is not None:
            req_queue_time: int = req_received - int(x_request_start)
            self.event_logger.on_request_received(int(req_received / 1_000), req_queue_time)

    def post_request(self, worker, req, environ, resp):
        self.logger.debug(
            f"post_request (w:{id(worker)} w.pid{worker.pid} rq:{id(req)} e:{id(environ)} rs:{id(resp)})")

    def worker_int(self, worker):
        self.logger.debug(f"worker_int (w:{id(worker)} w.pid{worker.pid})")

    def worker_exit(self, server, worker):
        self.logger.debug(f"worker_exit (s:{id(server)} s.pid{server.pid} w:{id(worker)} w.pid{worker.pid})")

    def child_exit(self, server, worker):
        self.logger.debug(f"child_exit (s:{id(server)} s.pid{server.pid} w:{id(worker)} w.pid{worker.pid})")

    def on_exit(self, server):
        self.logger.debug(f"on_exit (s:{id(server)} s.pid{server.pid})")
        self.reporter.stop()

    def on_reload(self, server):
        self.logger.debug(f"on_reload (s:{id(server)} s.pid{server.pid})")

    def worker_abort(self, worker):
        self.logger.debug(f"worker_abort (w:{id(worker)} w.pid{worker.pid})")

    def pre_exec(self, server):
        self.logger.debug(f"pre_exec ( s:{id(server)} s.pid{server.pid})")
