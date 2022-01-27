import asyncio
import datetime


class DynoscaleReporter:
    is_running = False

    def __init__(self):
        self.sleep_time = 2
        self.is_running = False
        self.start()

    def start(self):
        self.is_running = True
        asyncio.run(self.start_dumping_logs())

    def stop(self):
        self.is_running = False

    async def start_dumping_logs(self):
        while self.is_running:
            await asyncio.sleep(self.sleep_time)
            self.dump_logs()

    def dump_logs(self):
        print(f"{datetime.datetime.now()} is_running:{self.is_running} | a bunch of stuff")
