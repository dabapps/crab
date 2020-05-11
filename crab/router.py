from flask import Flask, Response, request, abort
from urllib.parse import urlparse
from werkzeug.routing import Rule
import os
import psutil
import requests
import sys


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


app = Flask(__name__, static_folder=None)
app.url_map.add(Rule("/", endpoint="proxy", defaults={"path": ""}))
app.url_map.add(Rule("/<path:path>", endpoint="proxy"))


@app.endpoint("proxy")
def proxy(path):
    routes = get_routes()
    hostname = urlparse(request.base_url).hostname
    if hostname not in routes:
        app.logger.warn("No backend for %s", hostname)
        abort(502)

    path = request.full_path if request.args else request.path
    target_url = "http://localhost:" + routes[hostname] + path
    app.logger.info(
        "Routing request to backend - %s %s%s", request.method, hostname, path
    )

    downstream_response = requests.request(
        method=request.method,
        url=target_url,
        headers=request.headers,
        data=request.get_data(),
        allow_redirects=False,
        stream=True,
    )

    # We need to remove the transfer-encoding header as this will
    # no longer apply to the response we are about to send
    downstream_response.raw.headers.pop("transfer-encoding", None)

    return Response(
        response=downstream_response.raw.data,
        status=downstream_response.status_code,
        headers=downstream_response.raw.headers.items(),
    )


def start_on_port(port):
    app.run(
        port=port,
        debug=True,
        use_debugger=False,
        use_reloader=False,
        load_dotenv=False,
        host=os.environ.get("CRAB_ROUTER_HOST"),
    )


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
