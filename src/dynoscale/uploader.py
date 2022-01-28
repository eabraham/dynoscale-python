import time
from threading import Thread, get_native_id, Event

from dynoscale.logger import RequestLogRepository
from dynoscale.utils import dlog


class EventUploader:
    """Provides methods to upload and/or print logs and clear them from the repository"""

    def __init__(self, repository: RequestLogRepository, upload_interval: int = 3, autostart: bool = False):
        dlog(f"EventUploader<{id(self)}>.__init__")
        self.repository = repository

        self.event = Event()

        self.upload_job = None
        self.upload_interval = upload_interval
        self.upload_job_started_at = None

        self.t = None
        if autostart:
            self.start()

    def start(self):
        dlog(f"EventUploader<{id(self)}>.start upload_interval is {self.upload_interval}s")
        self.upload_job_started_at = time.time()
        self.t = Thread(target=self.keep_uploading, args=(self,))
        self.t.start()
        # self.upload_job = asyncio.run(self.do_stuff_periodically(self.upload_interval, self.stuff))

    def stop(self):
        dlog(f"EventUploader<{id(self)}>.stop upload_interval is {self.upload_interval}s")
        if self.t is not None:
            self.event.set()
            self.t.join()

        if self.upload_job is not None:
            self.upload_job.cancel()
        self.upload_job = None

    def keep_uploading(self, self_in):
        dlog(f"EventUploader<{id(self)}>.keep_uploading - Starting to upload")
        repo = RequestLogRepository()

        while True:
            if self.event.is_set():
                dlog(f"EventUploader<{id(self)}>.keep_uploading - event set, stopping")
                break
            time.sleep(self.upload_interval)
            repo.dump_logs()

    def upload_logs(self):
        dlog(f"EventUploader<{id(self)}>.upload_logs")
        self.repository.dump_logs()
