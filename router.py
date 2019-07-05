from urllib.parse import urlparse
import os
import psutil
import asyncio
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
    async with ClientSession() as session:
        async with session.request(
            original_request.method,
            target_url,
            data=original_request.content,
            headers=original_request.headers,
        ) as response:
            proxied_response = web.Response(
                headers=response.headers, status=response.status
            )
            if response.headers.get("Transfer-Encoding", "").lower() == "chunked":
                proxied_response.enable_chunked_encoding()

            await proxied_response.prepare(original_request)
            try:
                async for data in response.content.iter_any():
                    await proxied_response.write(data)
            except ConnectionResetError:
                pass

        return proxied_response


async def start_on_port(port):
    loop = asyncio.get_event_loop()
    server = await loop.create_server(web.Server(handle), "0.0.0.0", port)
    print(f"Router listening on port {port}.")
    await server.serve_forever()


def run():
    if "CRAB_ROUTER_PORT" in os.environ:
        asyncio.run(start_on_port(int(os.environ["CRAB_ROUTER_PORT"])))
    else:
        try:
            asyncio.run(start_on_port(80))
        except:
            asyncio.run(start_on_port(8080))


if __name__ == "__main__":
    run()
