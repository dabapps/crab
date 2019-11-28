from flask import Flask, Response, request, abort
from urllib.parse import urlparse
from werkzeug.routing import Rule
import os
import psutil
import requests


def get_route_for_hostname(hostname):
    for process in psutil.process_iter(attrs=["environ"]):
        process_env = process.info["environ"]
        if (
            process_env
            and process_env.get("VIRTUAL_HOST") == hostname
            and "PORT" in process_env
        ):
            return process_env["PORT"]


app = Flask(__name__, static_folder=None)
app.url_map.add(Rule("/", endpoint="proxy", defaults={"path": ""}))
app.url_map.add(Rule("/<path:path>", endpoint="proxy"))


@app.endpoint("proxy")
def proxy(path):
    hostname = urlparse(request.base_url).hostname
    upstream_port = get_route_for_hostname(hostname)
    if not upstream_port:
        app.logger.warn(f"No backend for {hostname}")
        abort(502)

    path = request.full_path if request.args else request.path
    target_url = f"http://localhost:{upstream_port}{path}"
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


def start_on_port(port):
    app.run(
        port=port, debug=True, use_debugger=False, use_reloader=False, load_dotenv=False
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
