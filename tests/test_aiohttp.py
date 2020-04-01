from asyncio import AbstractEventLoop

import aiohttp
from aiohttp.client_exceptions import ClientConnectionError
import asyncio
import pytest
import requests
from async_generator import async_generator, yield_

from pytest_thawgun.plugin import ThawGun, wait_for

pytestmark = pytest.mark.asyncio

import json
import time
from contextlib import contextmanager, suppress, asynccontextmanager
from multiprocessing import Process
from typing import Dict

import requests
import uvicorn
from fastapi import FastAPI


def simple_app() -> FastAPI:
    app = FastAPI()

    @app.on_event("startup")
    async def setup_edge_direct_client() -> None:
        print("START APP")

    @app.get("/")
    async def delete_storage() -> str:
        print("Inside GET")
        return "abcd"

    return app


async def run_fun_async(fun, *args, **kwargs):
    return fun(*args, **kwargs)


async def run_uvicorn(app, **kwargs):
    print("START")
    uvicorn.run(app, **kwargs)
    print("STOP")


@asynccontextmanager
async def setup_and_teardown_fastapi_app(app: FastAPI, host: str, port: int, event_loop: AbstractEventLoop, session: aiohttp.ClientSession):
    """
    Manages setup of the provided app on a given `host` and `port` and its teardown.

    As for the setup process, the following things are done:
        * `/health` endpoint is added to the provided app,
        * The app is launched in a separate process,
        * function waits for the app to fully launch - to do this it repetitively checks `the /health`
         endpoint until it returns HTTP 200.

    Example use of this function in a fixture:

    >>> with setup_and_teardown_fastapi_app(FastAPI(), "localhost", 10000):
    >>>     yield

    :param app: app to launch
    :param host: host on which to launch app
    :param port: port on which to launch app
    """

    async def wait_until_app_healthy():
        timeout = 10
        start_time = time.time()
        healthy = False

        while not healthy and time.time() - start_time <= timeout:
            print(time.time() - start_time <= timeout)
            with suppress(ClientConnectionError):
                async with session.post(f"http://{host}:{port}/health") as rsp:
                    healthy = rsp.status == 200
            await asyncio.sleep(0.1)

        fail_message = f"Timeout expired: failed to start mock REST API in {timeout} seconds"
        assert healthy, fail_message

    app.post("/health")(lambda: "OK")

    # process = Process(target=uvicorn.run, args=(app,), kwargs={"host": host, "port": port, "loop": "asyncio"})
    # process.start()

    # task = event_loop.create_task(run_fun_async(print, "haha", "buu"))
    task = event_loop.create_task(run_uvicorn(app, host=host, port=port, loop="asyncio"))

    await wait_until_app_healthy()
    yield

    task.cancel()
    # await task

    # process.terminate()
    # process.join()


@pytest.fixture
async def server_url(event_loop, session) -> str:
    api_host = "localhost"
    api_port = 8080
    api_url = "http://localhost:8080"
    async with setup_and_teardown_fastapi_app(simple_app(), api_host, api_port, event_loop, session):
        yield api_url


@pytest.fixture
@async_generator
async def session(event_loop: AbstractEventLoop) -> aiohttp.ClientSession:
    async with aiohttp.ClientSession(loop=event_loop) as session:
        return await yield_(session)


async def call_endpoint_in_one_minute(session, url, iter_count=2):
    result = ""
    total_time = 60
    single_sleep_time = int(total_time / iter_count)
    print("Single sleep time", single_sleep_time, "s")
    for i in range(iter_count):
        print("Iteration", i)
        await asyncio.sleep(single_sleep_time)
        print("Send GET", i)
        # result = "abcd"
        async with session.get(url) as rsp:
            print("Receive GET", i)
            result = await rsp.text()
    return result


# async def test_get_in_task_timeout(session: aiohttp.ClientSession, server_url: str, thawgun: ThawGun):
#     task = thawgun.loop.create_task(call_endpoint_in_one_minute(session, server_url))
#     with thawgun as t:
#         await t.advance(59)
#         with pytest.raises(TimeoutError):
#             assert "abcd" in await wait_for(task, 1.0, loop=thawgun.loop)


async def test_get_in_task(session: aiohttp.ClientSession, server_url: str, thawgun: ThawGun):
    task = thawgun.loop.create_task(call_endpoint_in_one_minute(session, server_url))
    with thawgun as t:
        await t.advance(61)
        assert "abcd" in await wait_for(task, 1.0, loop=thawgun.loop)


if __name__ == "__main__":
    pass
