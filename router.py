from urllib.parse import urlparse
import os
import psutil
from aiohttp import web, ClientSession


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


async def handle(original_request):
    routes = get_routes()
    hostname = urlparse(str(original_request.url)).hostname
    if hostname not in routes:
        print(f"No backend for {hostname}")
        return web.Response(status=404)
    target_url = f"http://localhost:{routes[hostname]}{original_request.path_qs}"
    print(f"Routing to {target_url}")
    async with ClientSession(auto_decompress=False) as session:
        async with session.request(
            original_request.method,
            target_url,
            data=original_request.content,
            headers=original_request.headers,
            allow_redirects=False,
        ) as response:
            proxied_response = web.StreamResponse(
                headers=response.headers, status=response.status
            )
            if response.headers.get("Transfer-Encoding", "").lower() == "chunked":
                proxied_response.enable_chunked_encoding()
            await proxied_response.prepare(original_request)
            async for data in response.content.iter_any():
                await proxied_response.write(data)
            return proxied_response


def run():
    application = web.Application()
    application.router.add_route("*", r"/{path:.*}", handle)
    web.run_app(
        application, host="0.0.0.0", port=int(os.environ.get("CRAB_ROUTER_PORT", 80))
    )


if __name__ == "__main__":
    run()
