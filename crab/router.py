from flask import Flask, Response, request, abort
from urllib.parse import urlparse
from werkzeug.routing import Rule
import os
import psutil
import requests
import argparse
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
        app.logger.warn(f"No backend for {hostname}")
        abort(502)

    path = request.full_path if request.args else request.path
    target_url = f"http://localhost:{routes[hostname]}{path}"
    app.logger.info(f"Routing request to backend - {request.method} {hostname}{path}")

    downstream_response = requests.request(
        method=request.method,
        url=target_url,
        headers=request.headers,
        data=request.get_data(),
        allow_redirects=False,
        stream=True,
    )
    return Response(
        response=downstream_response.raw.data,
        status=downstream_response.status_code,
        headers=downstream_response.raw.headers.items(),
    )


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--expose",
        action="store_true",
        help="Allow crab to be accessed outside the local machine",
    )
    return parser.parse_args(sys.argv[2:])


def start_on_port(args, port):
    app.run(
        port=port,
        debug=True,
        use_debugger=False,
        use_reloader=False,
        load_dotenv=False,
        host="0.0.0.0" if args.expose else None,
    )


def run():
    args = get_args()

    if "CRAB_ROUTER_PORT" in os.environ:
        start_on_port(int(os.environ["CRAB_ROUTER_PORT"]))
    else:
        try:
            start_on_port(args, 80)
        except:
            start_on_port(args, 8080)


if __name__ == "__main__":
    run()
