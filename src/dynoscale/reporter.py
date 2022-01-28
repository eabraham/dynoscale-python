import asyncio
import datetime

from dynoscale.utils import dlog


class DynoscaleReporter:
    is_running = False

    def __init__(self):
        dlog(f"DynoscaleReporter<{id(self)}>.__init__")
        self.sleep_time = 2
        self.is_running = False
        self.start()

    def start(self):
        dlog(f"DynoscaleReporter<{id(self)}>.start")
        self.is_running = True
        asyncio.run(self.start_dumping_logs())

    def stop(self):
        dlog(f"DynoscaleReporter<{id(self)}>.stop")
        self.is_running = False

    async def start_dumping_logs(self):
        dlog(f"DynoscaleReporter<{id(self)}>.start_dumping_logs")
        while self.is_running:
            await asyncio.sleep(self.sleep_time)
            self.dump_logs()

    def dump_logs(self):
        dlog(f"DynoscaleReporter<{id(self)}>.dump_logs")
