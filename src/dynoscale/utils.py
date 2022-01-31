import math
import os
import random
import threading
import time

from dynoscale.const.header import X_REQUEST_START


# TODO: Decide if I should keep this for devs to test locally or remove
def mock_in_heroku_headers(req):
    # Fake request start to something up to a second ago
    req.headers.append(
        (X_REQUEST_START, str(math.floor(time.time_ns() / 1_000_000) - random.randint(10, 1_000)))
    )


def extract_header_value(req, header_key: str):
    values = [value for key, value in req.headers if key.lower() == header_key.lower()]
    return values[0] if len(values) > 0 else None


def write_header_value(req, key: str, value: str):
    req.headers.append((key, value))


def epoch_s():
    return math.floor(time.time_ns() / 1_000_000_000)


def epoch_ms():
    return math.floor(time.time_ns() / 1_000_000)


def epoch_us():
    return math.floor(time.time_ns() / 1_000)


def epoch_ns():
    return time.time_ns()


def dlog(msg: str):
    print(f"pid-{os.getpid():03} ppid-{os.getppid():03} thread-{threading.get_ident():03}: {msg}")
