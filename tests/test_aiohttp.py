import contextlib
import time
from asyncio import AbstractEventLoop, wait_for
from multiprocessing import Process

import aiohttp
import asyncio
import pytest
import requests
from async_generator import async_generator, yield_
from flask import Flask, request
from flask_restful import Api, Resource
from werkzeug import run_simple

from pytest_thawgun.plugin import ThawGun

pytestmark = pytest.mark.asyncio


def wait_for_api_to_be_accessible(url: str, timeout: int = 10, poll_interval: int = 1):
    """
    Waits for mock REST API to be accessible to requests.

    :param url: url of the service
    :param timeout: how many seconds the script will wait for REST API to be accessible
    :param poll_interval: how often REST API will be polled
    """
    response = requests.Response()
    response.status_code = 404
    start_time = time.time()
    while response.status_code != 200 and time.time() - start_time <= timeout:
        with contextlib.suppress(requests.exceptions.ConnectionError):
            response = requests.request("GET", url)
        time.sleep(poll_interval)
    assert response.status_code == 200, "Timeout expired: failed to start mock REST API in {} seconds".format(timeout)


@pytest.fixture
def server_url() -> str:
    app = Flask(__name__)
    api = Api(app)
    api_host = "localhost"
    api_port = 8080
    api_url = "http://localhost:8080"

    class HelloWorld(Resource):
        def get(self):
            return "abcd"

    class Shutdown(Resource):
        @staticmethod
        def post():
            shutdown_function = request.environ.get("werkzeug.server.shutdown")

            if shutdown_function is None:
                raise RuntimeError("Not running with the Werkzeug Server")

            shutdown_function()
            return "Server shutting down...", 200

    api.add_resource(HelloWorld, '/')
    api.add_resource(Shutdown, '/down')

    flask_app_process = Process(name="PlatformAPIMock", target=run_simple,
                                kwargs=dict(hostname=api_host,
                                            port=api_port,
                                            application=app,
                                            use_debugger=True, use_reloader=False))
    flask_app_process.start()
    wait_for_api_to_be_accessible(api_url)
    yield api_url

    requests.request("POST", api_url + "/down")

    if flask_app_process.is_alive():
        flask_app_process.join()


@pytest.fixture
@async_generator
async def session(event_loop: AbstractEventLoop) -> aiohttp.ClientSession:
    async with aiohttp.ClientSession() as session:
        return await yield_(session)


async def call_endpoint_in_one_minute(session, url):
    await asyncio.sleep(60)
    async with session.get(url) as rsp:
        return await rsp.text()


async def test_get_in_task(session: aiohttp.ClientSession, server_url: str, thawgun: ThawGun):
    task = thawgun.loop.create_task(call_endpoint_in_one_minute(session, server_url))
    with thawgun as t:
        await t.advance(60)
        assert "abcd" in await wait_for(task, 0.1, loop=thawgun.loop)
