import time
from threading import Thread, get_native_id

from dynoscale.logger import RequestLogRepository


class EventUploader:
    """Provides methods to upload and/or print logs and clear them from the repository"""

    def __init__(self, repository: RequestLogRepository, upload_interval: int = 3, autostart: bool = False):
        print(f"thread-{get_native_id()}: Initializing EventUploader")
        self.repository = repository
        self.upload_job = None
        self.upload_interval = upload_interval
        self.upload_job_started_at = None

        self.t = None
        if autostart:
            self.start()

    def start(self):
        print(f"thread-{get_native_id()}: EventUploader:starting upload_interval is {self.upload_interval}s")
        self.upload_job_started_at = time.time()
        self.t = Thread(target=self.keep_uploading, args=(self,))
        self.t.start()
        # self.upload_job = asyncio.run(self.do_stuff_periodically(self.upload_interval, self.stuff))

    def stop(self):
        print(f"thread-{get_native_id()}: EventUploader:stopping upload_interval is {self.upload_interval}s")
        if self.t is not None:
            self.t.join()

        if self.upload_job is not None:
            self.upload_job.cancel()
        self.upload_job = None

    def keep_uploading(self, self_in):
        while True:
            time.sleep(self.upload_interval)
            self_in.upload_logs()

    def upload_logs(self):
        print(f"thread-{get_native_id()}: EventUploader - Uploading logs")
        self.repository.dump_logs()
