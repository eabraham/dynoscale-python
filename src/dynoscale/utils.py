import logging
import math
import os
import random
import threading
import time

from dynoscale.const.header import X_REQUEST_START

logger = logging.getLogger(__name__)


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


def prepend_thread_info(msg: str):
    return f"t{threading.get_ident()} {msg}"


def prepend_process_info(msg: str):
    return f"p{os.getpid()} pp{os.getppid()} {msg}"


def log_d(msg: str):
    logger.debug(msg=prepend_process_info(prepend_thread_info(msg)))


def log_i(msg: str):
    logger.info(msg=prepend_process_info(prepend_thread_info(msg)))


def log_w(msg: str):
    logger.warning(msg=prepend_process_info(prepend_thread_info(msg)))


def log_e(msg: str):
    logger.error(msg=prepend_process_info(prepend_thread_info(msg)))


def log_c(msg: str):
    logger.critical(msg=prepend_process_info(prepend_thread_info(msg)))
