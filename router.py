import os

import httpx
import psutil
import uvicorn
from starlette.applications import Starlette
from starlette.middleware.cors import ALL_METHODS
from starlette.responses import Response, StreamingResponse
from starlette.routing import Route


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
            allow_redirects=False
        )
        if not upstream_response.is_stream_consumed:
            return StreamingResponse(
                content=upstream_response.stream(),
                status_code=upstream_response.status_code,
                headers=upstream_response.headers,
            )

        upstream_response_body = await upstream_response.read()
        return Response(
            content=upstream_response_body,
            status_code=upstream_response.status_code,
            headers=upstream_response.headers,
        )


app = Starlette(routes=[Route("/(.*)", endpoint=proxy, methods=ALL_METHODS)])


def start_on_port(port):
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
