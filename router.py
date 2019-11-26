import os

import httpx
import psutil
import uvicorn
from starlette.applications import Starlette
from starlette.middleware.cors import ALL_METHODS
from starlette.responses import StreamingResponse, Response
from starlette.routing import Route
from uvicorn.config import LOGGING_CONFIG as UVICORN_LOGGING_CONFIG
from uvicorn.logging import AccessFormatter


def get_routes():
    routes = {}
    for process in psutil.process_iter(attrs=["environ"]):
        try:
            host = process.info["environ"]["VIRTUAL_HOST"]
            port = process.info["environ"]["PORT"]
            routes[host] = port
        except:
            pass
    return routes


class CustomAccessFormatter(AccessFormatter):
    def get_client_addr(self, scope):
        """
        _Pretend_ the client address is actually the hostname.
        Makes the log messages much nicer!
        """
        if 'headers' not in scope:
            return super().get_client_addr(scope)
        return httpx.Headers(scope['headers'])['Host']


async def proxy(request):
    routes = get_routes()
    hostname = request.url.hostname
    if hostname not in routes:
        return Response(status_code=502)
    path = request.url.path
    target_url = f"http://localhost:{routes[hostname]}{path}"
    body = await request.body()
    async with httpx.AsyncClient() as client:
        upstream_response = await client.request(
            method=request.method,
            url=target_url,
            data=body,
            headers=request.headers.raw,
            allow_redirects=False,
            stream=True
        )
        return StreamingResponse(
            content=upstream_response.raw(),
            status_code=upstream_response.status_code,
            headers=upstream_response.headers,
        )


app = Starlette(routes=[Route("/(.*)", endpoint=proxy, methods=ALL_METHODS)])


def start_on_port(port):
    UVICORN_LOGGING_CONFIG['formatters']['access']['()'] = CustomAccessFormatter
    uvicorn.run(app, port=port, host="0.0.0.0")


def run():
    if "CRAB_ROUTER_PORT" in os.environ:
        start_on_port(int(os.environ["CRAB_ROUTER_PORT"]))
    else:
        try:
            start_on_port(80)
        except:
            start_on_port(8080)


if __name__ == "__main__":
    run()
