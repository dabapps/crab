from crab.router import get_routes
from unittest import TestCase
import subprocess
import os


class RouterTestCase(TestCase):
    def test_get_routes(self):
        with subprocess.Popen(
            ["sleep", "5"],
            env={**os.environ, "VIRTUAL_HOST": "test.localhost", "PORT": "1234"},
        ) as subproc:
            routes = get_routes()
            self.assertEqual(routes, {"test.localhost": "1234"})
            subproc.terminate()
