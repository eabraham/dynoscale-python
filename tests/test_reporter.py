import asyncio
import contextlib
import os
import uuid

import pytest
import requests
import responses

from dynoscale.logger import RequestLogRepository
from dynoscale.reporter import DynoscaleReporter, DEFAULT_SECONDS_BETWEEN_REPORTS, DEFAULT_SECONDS_BETWEEN_DB_VACUUM

API_URL_EMPTY = ''

HTTP_SERVER = "localhost"
HTTP_PORT = 8888

API_PROTOCOL = "https"
API_HOST = f"{HTTP_SERVER}"
API_PORT = f":{HTTP_PORT}"
API_PATH = '/api/v1'
API_COMMAND = '/report'
API_TOKEN = '/nzhjmzvknditndu1mc00n'
API_ROUTE = f"{API_PATH}{API_COMMAND}{API_TOKEN}"
API_URL = f"{API_PROTOCOL}://{API_HOST}{API_PORT}{API_ROUTE}"

REPOSITORY_FILENAME = "dynoscale_test_repo.sqlite3"

RESPONSE_DEFAULT_JSON = {
    'config': {
        'publish_frequency': 30
    }
}


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def ds_reporter():
    reporter = DynoscaleReporter(
        api_url="",
        autostart=False,
        repository_filename=REPOSITORY_FILENAME,
    )
    yield reporter
    reporter.stop()
    with contextlib.suppress(FileNotFoundError):
        os.remove(REPOSITORY_FILENAME)


@pytest.fixture
def ds_log_repository():
    request_log_repository = RequestLogRepository(
        filename=REPOSITORY_FILENAME
    )
    yield request_log_repository
    with contextlib.suppress(FileNotFoundError):
        os.remove(REPOSITORY_FILENAME)


@responses.activate
def test_responses_https():
    url = 'https://twitter.com/api/1/foobar'
    responses.add(
        responses.GET,
        url,
        json={'error': 'not found'},
        status=404
    )

    resp = requests.get(url)

    assert resp.json() == {"error": "not found"}

    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == url
    assert responses.calls[0].response.text == '{"error": "not found"}'


def test_reporter_construction():
    with pytest.raises(TypeError) as error:
        # noinspection PyArgumentList
        DynoscaleReporter()
    assert TypeError is error.type

    reporter = DynoscaleReporter(API_URL_EMPTY)

    assert reporter
    assert DEFAULT_SECONDS_BETWEEN_REPORTS == reporter.report_period
    assert DEFAULT_SECONDS_BETWEEN_DB_VACUUM == reporter.vacuum_period
    assert API_URL_EMPTY == reporter.api_url


def test_not_autostarted_by_default(ds_reporter):
    assert not ds_reporter.loop


def test_autostart_works():
    reporter = DynoscaleReporter(api_url=API_URL, autostart=True)
    assert reporter.loop
    reporter.stop()


def test_manual_start(ds_reporter):
    ds_reporter.start()
    assert ds_reporter.loop.is_running()


@pytest.mark.asyncio
async def test_manual_stop():
    reporter = DynoscaleReporter(API_URL_EMPTY)
    reporter.start()
    await asyncio.sleep(0.1)
    reporter.stop()
    assert not reporter.loop


@pytest.mark.asyncio
@responses.activate
async def test_report_payload_format(mocked_responses, ds_log_repository, ds_reporter):
    url = API_URL + f"-test-payload-{uuid.uuid4()}"
    mocked_responses.add(responses.POST, url, json=RESPONSE_DEFAULT_JSON, status=200)
    ds_log_repository.add_queue_time(123456789, 0)
    payload = '123456789,0,web,\r\n'

    ds_reporter.api_url = url
    ds_reporter.report_period = 0
    ds_reporter.start()
    await asyncio.sleep(.5)

    assert len(mocked_responses.calls) == 1
    assert mocked_responses.calls[0].request.url == url
    assert mocked_responses.calls[0].request.body == payload
    assert mocked_responses.calls[0].response.json() == RESPONSE_DEFAULT_JSON


@pytest.mark.asyncio
@responses.activate
async def test_update_publish_frequency(mocked_responses, ds_log_repository, ds_reporter):
    url = API_URL + f"-test-update-publish-frequency-{uuid.uuid4()}"
    publish_frequency = 99
    resp_json = {
        'config': {
            'publish_frequency': publish_frequency
        }
    }
    mocked_responses.add(responses.POST, url, json=resp_json, status=200)
    ds_log_repository.add_queue_time(111111111, 2)
    ds_log_repository.add_queue_time(333333333, 4)
    payload = '111111111,2,web,\r\n' \
              '333333333,4,web,\r\n'

    ds_reporter.api_url = url
    ds_reporter.report_period = 0
    ds_reporter.start()
    await asyncio.sleep(.5)

    assert len(mocked_responses.calls) == 1
    assert mocked_responses.calls[0].request.url == url
    assert mocked_responses.calls[0].request.body == payload
    assert mocked_responses.calls[0].response.json() == resp_json
    assert ds_reporter.report_period == publish_frequency
