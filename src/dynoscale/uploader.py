import asyncio
import random
import threading
import time
from pprint import pprint

from dynoscale.logger import RequestLogRepository


class EventUploader:
    """Provides methods to upload and/or print logs and clear them from the repository"""

    def __init__(self, repository: RequestLogRepository, upload_interval: int = 5, autostart: bool = False):
        print(f"thread-{threading.get_native_id()}: Initializing EventUploader")
        self.repository = repository
        self.upload_job = None
        self.upload_interval = upload_interval
        self.upload_job_started_at = None
        if autostart:
            self.start()

    def start(self):
        print(f"thread-{threading.get_native_id()}: EventUploader:starting upload_interval is {self.upload_interval}s")
        self.upload_job_started_at = time.time()
        self.upload_job = asyncio.run(self.do_stuff_periodically(self.upload_interval, self.stuff))

    def stop(self):
        print(f"thread-{threading.get_native_id()}: EventUploader:stopping upload_interval is {self.upload_interval}s")
        if self.upload_job is not None:
            self.upload_job.cancel()
        self.upload_job = None

    async def do_stuff_periodically(self, interval, periodic_function):
        while True:
            print(round(time.time() - self.upload_job_started_at, 1), "Starting periodic function")
            await asyncio.gather(
                asyncio.sleep(interval),
                periodic_function(),
            )

    async def stuff(self):
        self.upload_logs()
        await asyncio.sleep(random.random() * 1.5)

    def upload_logs(self):
        print(
            f"thread-{threading.get_native_id()}: EventUploader - Uploading logs @{time.time()} started@ {self.upload_job_started_at}")
        print(f"For now printing self.repository.request_logs:")
        pprint(self.repository.request_logs)
