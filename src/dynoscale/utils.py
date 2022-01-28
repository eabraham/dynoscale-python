import math
import os
import random
import threading
import time
import uuid

from dynoscale.const.header import X_REQUEST_START, X_REQUEST_ID, CONNECT_TIME, TOTAL_ROUTE_TIME


# TODO: Decide if I should keep this for devs to test locally or remove
def mock_in_heroku_headers(req):
    # Fake request start to something up to a second ago
    req.headers.append(
        (X_REQUEST_START, str(math.floor(time.time_ns() / 1_000_000) - random.randint(10, 1_000)))
    )
    # Fake request id, Heroku does uuid4 so prepend with GID for GunicornID
    req.headers.append((X_REQUEST_ID, 'MOCK-' + str(uuid.uuid4())))
    # Fake connect time, don't know what this is yet
    req.headers.append((CONNECT_TIME, str(random.randint(0, 500))))
    # Fake total route time, don't know what this is yet
    req.headers.append((TOTAL_ROUTE_TIME, str(random.randint(0, 250))))


def extract_header_value(req, header_key: str):
    values = [value for key, value in req.headers if key.lower() == header_key.lower()]
    return values[0] if len(values) > 0 else None


def write_header_value(req, key: str, value: str):
    req.headers.append((key, value))


def dlog(msg: str):
    print(f"ppid-{os.getppid():05} pid-{os.getpid():05} thread-{threading.get_native_id()}: {msg}")